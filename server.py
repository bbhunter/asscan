#!/usr/bin/env python3

import tornado.ioloop
import tornado.web
from multiprocessing import Process, Queue
import json
from scanners import *
from scrapers import *
from results import *
import re
from os.path import join
import collections
import ipaddress
re_uuid = re.compile('^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z', re.I)

# queues for tasks of different kinds. The maxsize parameter determines
# how many tasks can be active in parallel at any given time
massqueue = Queue(maxsize = 1)
nmapqueue = Queue(maxsize = 4)
vulnqueue = Queue(maxsize = 16)
scraperqueue = Queue(maxsize = 8)

alljobs = {}

def forkjob(job, queue):
    def task():
        sys.stderr.write("Queueing %s\n"%job.ident)
        queue.put(job.ident)
        alljobs[job.ident] = job
        job.scan()
        del alljobs[job.ident]
        x=queue.get()
        sys.stderr.write("Removed %s from queue\n"%x)
        sys.stderr.write("Queue length %d\n"%queue.qsize())
    p = Process(target = task)
    p.start()

class ScansHandler(tornado.web.RequestHandler):
    def get(self):
        # Returns all past scans
        r=Results()
        r.read_all('results')
        self.write({'scans': sorted(r.scans, key=lambda x:x['target'])})
    

class ResultsHandler(tornado.web.RequestHandler):
    def get(self, shit):
        # Returns results from all scans
        # The web UI only uses the /filter? api
        args = shit.split('/')

        if args[0] == 'ip': # single result by ip, /results/ip/192.168.0.1
            ip = args[1]
            r = Results()
            r.read_all('results')
            if ip in r.hosts.keys():
                self.write({ip: r.hosts[ip]})
            else:
                self.write({'ip': {}})
        elif args[0] == 'port':
            port = args[1]
            r = Results()
            r.read_all('results')
            self.write(r.by_port(port))
        elif args[0] == 'filter':
            prefix = self.get_query_argument('prefix', None)
            port = self.get_query_argument('port', None)
            service = self.get_query_argument('service', None)
            vulns = self.get_query_argument('vulns', None)
            screenshots = self.get_query_argument('screenshots', None)
            r = Results()
            r.read_all('results')
            filtered = r.hosts
            if prefix and len(prefix) > 0:
                if not prefix[-1] == '.':
                    prefix += '.'
                filtered = filter_by_prefix(filtered, prefix)
            if port and len(port) > 0:
                filtered = filter_by_port(filtered, port)
            if service and len(service) > 0:
                filtered = filter_by_service(filtered, service)
            if vulns and vulns == 'true':
                filtered = filter_by_vulns(filtered)
            if screenshots and screenshots == 'true':
                filtered = filter_by_vulns(filtered)
            self.write({'ips':list(filtered.keys())})
        elif args[0] == 'all':
            r = Results()
            r.read_all('results')
            self.write(r.hosts)
        elif args[0] == 'networks': # i don't think this is used currently
            r = Results()
            r.read_all('results')
            counts = collections.defaultdict(int)
            for key in r.hosts.keys():
                k = '.'.join(key.split('.')[:2])
                counts[k] += 1
            self.write(dict(counts))
        elif args[0] == 'ips':
            r = Results()
            r.read_all('results')
            self.write({'ips':sorted(list(r.hosts.keys()))})
        elif re_uuid.match(args[0]): # some scans save files, this returns them
            filepath = join('results', *args)
            if filepath.endswith('.png'):
                self.set_header('content-type', 'image/png')
                self.write(open(filepath,'rb').read())
            if filepath.endswith('.jpg'):
                self.set_header('content-type', 'image/jpg')
                self.write(open(filepath,'rb').read())
            else:
                self.set_header('content-type', 'text/plain')
                self.write(open(filepath,'rb').read())
        else:
            self.write({"status": "not ok"}) # what

# information on current scan jobs
class JobsHandler(tornado.web.RequestHandler):
    def get(self, shit):
        args = shit.split('/')
        if args[0] == 'overview':
            jobs = {'nmap': nmapqueue.qsize(),
                    'masscan': massqueue.qsize(),
                    'scrapers': scraperqueue.qsize(),
                    'vuln': vulnqueue.qsize()}
            self.write(jobs)
        elif args[0] == 'status':
            status = {}
            for key in alljobs.keys():
                status[key] = alljobs[key].status
            self.write(status)
        else:
            self.write({'error': 'fuck off'})
            

    # submits a new scan job
    def post(self, args):
        typ = self.get_query_argument('type')
        foundonly = self.get_query_argument('found_only', False) # when set, only scan hosts found with eg. masscan earlier
        if foundonly == 'false' or foundonly == '0': # how stringly
            foundonly = False
        target = self.get_query_argument("target", None)
        mask = self.get_query_argument("mask", None)
        maxmask = self.get_query_argument('maxmask', None)
        hostkeys = None
        if ',' in target:
            hostkeys = target.replace(' ','').split(',')
        
        if not target or not mask:
            self.write({'status': 'fuck off',
                        'reason': 'target or mask missing'})
            return

        if typ == 'masscan':
            targetspec = [target + '/' + mask]
            jobids = []
            port = self.get_query_argument('port', None)

            # split a netmask N scan into smaller scans of mask M
            # 10.0.0.0/8 with submask /9 --> two scans
            # /16 scans are kinda ok with /19 scans, for example
            if maxmask: 
                targetspec = []
                for x in ipaddress.ip_network(target + '/' + mask).subnets(new_prefix = int(maxmask)):
                    targetspec.append(str(x.network_address) + '/' + maxmask)
            for t in targetspec:
                if port and len(port) > 0: # custom port
                    job = Masscan(t, ports = port.replace(' ',''))
                else: # default port list, see the masscan class
                    job = Masscan(t)
                forkjob(job, massqueue)
                jobids.append(job.ident)
            self.write({'jobs': jobids})
        elif typ == 'nmap':
            if foundonly: # only scan hosts found earlier with masscan
                r = Results()
                r.read_all('results')
                hosts = filter_by_network(r.hosts, target, mask)
                hosts = filter_by_missing_scan(r.hosts, 'nmap')
                hostkeys = list(hosts.keys())
                n = 32
                hostkeylists = [hostkeys[i * n:(i + 1) * n] for i in range((len(hostkeys) + n - 1) // n )]
                jobids = []
                for kl in hostkeylists:
                    job = Nmap(kl)
                    forkjob(job, nmapqueue)
                    jobids.append(job.ident)
                self.write({'jobs': jobids})
            else:
                targetspec = [target + '/' + mask]
                jobids = []
                if maxmask:
                    targetspec = []
                    for x in ipaddress.ip_network(target + '/' + mask).subnets(new_prefix = int(maxmask)):
                        targetspec.append(str(x.network_address) + '/' + maxmask)
                for t in targetspec:
                    job = Nmap(t)
                    forkjob(job, nmapqueue)
                    jobids.append(job.ident)
                self.write({'jobs': jobids})
        elif typ == 'nmap-udp': # TODO missing the foundonly flag handling!
            udp = True
            targetspec = None
            prefix = self.get_query_argument('prefix', None)
            job = Nmap(targetspec, udp=True)
            forkjob(job, nmapqueue)
            self.write({'jobid': job.ident})
        elif typ == 'smbvuln': # check if this still works. OTOH ms17-010 has its own checker now
            targetspec = target + '/' + mask
            job = SmbVuln(targetspec)
            forkjob(job, vulnqueue)
            self.write({'jobid': job.ident})
        elif typ == 'webscreenshot':
            # Fetch results for target subnet, only screenshot those with open ports
            port = self.get_query_argument('port', '80')
            scheme = self.get_query_argument('scheme', 'http')
            r = Results()
            r.read_all('results')
            hosts = r.hosts
            hosts = filter_by_network(hosts, target, mask)
            if foundonly: # better have this set, or hardcode
                hosts = filter_by_port(hosts, port)
            hostkeys = list(hosts.keys())
            if mask == '32':
                hostkeys = [target]
            job = WebScreenshot(list(hosts.keys()), scheme, port)
            forkjob(job, scraperqueue)
            self.write({'jobid': job.ident})
        elif typ == 'rdpscreenshot':
            port = self.get_query_argument('port', '3389') # default port only
            r = Results()
            r.read_all('results')
            hosts = r.hosts
            hosts = filter_by_network(hosts, target, mask)
            if foundonly:
                hosts = filter_by_port(hosts, port)
            hostkeys = list(hosts.keys())
            if mask == '32':
                hostkeys = [target]
            print('hostkeys %s'%str(hostkeys))
            job = RdpScreenshot(hostkeys)
            forkjob(job, scraperqueue)
            self.write({'jobid': job.ident})
        elif typ == 'vncscreenshot':
            # Fetch results for target subnet, only screenshot those with open ports
            port = self.get_query_argument('port', '5901') # UI should set this
            r = Results()
            r.read_all('results')
            hosts = r.hosts
            hosts = filter_by_network(hosts, target, mask)
            if foundonly:
                hosts = filter_by_port(hosts, port)
            hostkeys = list(hosts.keys())
            if mask == '32':
                hostkeys = [target]
            print('hostkeys %s'%str(hostkeys))
            job = VncScreenshot(hostkeys, port=port)
            forkjob(job, scraperqueue)
            self.write({'jobid': job.ident})
        elif typ == 'enum4linux':
            # Fetch results for target subnet, only screenshot those with open ports
            r = Results()
            r.read_all('results')
            hosts = r.hosts
            hostkeys = []
            hosts = filter_by_network(hosts, target, mask)
            print('filtered: %s'%str(hosts.keys()))
            if foundonly:
                hosts = filter_by_port(hosts, '445') # should this be 139 or 445?
            hostkeys = list(hosts.keys())
            if mask == '32':
                hostkeys = [target]
            job = Enum4Linux(hostkeys)
            forkjob(job, scraperqueue)
            self.write({'jobid': job.ident})
        elif typ == 'snmpwalk':
            # Fetch results for target subnet, only screenshot those with open ports
            prefix = self.get_query_argument('prefix', None)
            r = Results()
            r.read_all('results')
            hosts = r.hosts
            hosts = filter_by_network(hosts, target, mask)
            hostkeys = list(hosts.keys())
            if mask == '32':
                hostkeys = [target]
            job = Snmpwalk(hostkeys)
            forkjob(job, scraperqueue)
            self.write({'jobid': job.ident})
        elif typ == 'ffuf':
            # Fetch results for target subnet, only screenshot those with open ports
            port = self.get_query_argument('port', '80')
            r = Results()
            r.read_all('results')
            hosts = r.hosts
            hosts = filter_by_network(hosts, target, mask)
            if foundonly:
                sys.stderr.write('0: %s\n'%str(list(hosts.keys())))
                hosts = filter_by_port(hosts, port)
                sys.stderr.write('1: %s\n'%str(list(hosts.keys())))
            hostkeys = list(hosts.keys())
            job = Ffuf(hostkeys)
            forkjob(job, scraperqueue)
            self.write({'jobid': job.ident})
        elif typ == 'bluekeep':
            # Fetch results for target subnet, only screenshot those with open ports
            port = '3389'
            r = Results()
            r.read_all('results')
            hosts = r.hosts
            hosts = filter_by_network(hosts, target, mask)
            if foundonly:
                sys.stderr.write('0: %s\n'%str(list(hosts.keys())))
                hosts = filter_by_port(hosts, port)
                sys.stderr.write('1: %s\n'%str(list(hosts.keys())))
            hostkeys = list(hosts.keys())
            job = Bluekeep(hostkeys)
            forkjob(job, scraperqueue)
            self.write({'jobid': job.ident})
        elif typ == 'ms17_010':
            # Fetch results for target subnet, only screenshot those with open ports
            port = '445'
            r = Results()
            r.read_all('results')
            hosts = r.hosts
            hosts = filter_by_network(hosts, target, mask)
            if foundonly:
                sys.stderr.write('0: %s\n'%str(list(hosts.keys())))
                hosts = filter_by_port(hosts, port)
                sys.stderr.write('1: %s\n'%str(list(hosts.keys())))
            hostkeys = list(hosts.keys())
            job = Ms17_010(hostkeys)
            forkjob(job, scraperqueue)
            self.write({'jobid': job.ident})
        elif typ == 'sleep':
            job = SleepJob()
            forkjob(job, nmapqueue)
        else:
            self.write({'error': 'unknown job type'})
            


def make_app():
    return tornado.web.Application([
        (r"/jobs/(.*)", JobsHandler),
        (r"/api/jobs/(.*)", JobsHandler), # /api for the vue dev server api router
        (r"/api/results/(.*)", ResultsHandler), # ditto
        # route /ui to the vue app built with 'npm run build', no need to copy it
        (r"/ui/(.*)", tornado.web.StaticFileHandler, {"path": "ui/asscan/dist/",\
                                                      "default_filename": 'index.html'}),
        (r"/js/(.*)", tornado.web.StaticFileHandler, {"path": "ui/asscan/dist/js/"}),
        (r"/css/(.*)", tornado.web.StaticFileHandler, {"path": "ui/asscan/dist/css/"}),
        (r"/results/(.*)", ResultsHandler),
        (r"/scans/", ScansHandler),
        (r"/api/scans/", ScansHandler),
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": "ui/asscan/dist/",\
                                                   "default_filename": 'index.html'}),
    ])

def main():
    app = make_app()
    app.listen(8888, address='127.0.0.1') # better not expose this
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()
