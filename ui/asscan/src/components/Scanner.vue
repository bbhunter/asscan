<template>
  <div>
    <form class="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4">
      <div class="flex items-center justify-center">
        <div
          class="bg-blue-500 text-white py-2 px-2 m-2 rounded focus:outline-none focus:shadow-outline"
        >
          <input
            type="checkbox"
            name="scantype"
            value="masscan"
            v-model="values.masscan"
            class="mr-1 bg-gray-300 text-gray-800 py-2 px-4 rounded-l"
          />masscan
        </div>

        <div
          class="bg-blue-500 text-white py-2 px-2 m-2 rounded focus:outline-none focus:shadow-outline"
        >
          <input
            type="checkbox"
            name="scantype"
            value="nmap"
            v-model="values.nmap"
            class="mr-1 bg-gray-300 text-gray-800 py-2 px-4 rounded-l"
          />nmap
        </div>
        <div
          class="bg-blue-500 text-white py-2 px-2 m-2 rounded focus:outline-none focus:shadow-outline"
        >
          <input
            type="checkbox"
            name="scantype"
            value="ffuf"
            v-model="values.ffuf"
            class="mr-1 bg-gray-300 text-gray-800 py-2 px-4 rounded-l"
          />ffuf
        </div>
        <div
          class="bg-blue-500 text-white py-2 px-2 m-2 rounded focus:outline-none focus:shadow-outline"
        >
          <input
            type="checkbox"
            name="scantype"
            value="snmpwalk"
            v-model="values.snmp"
            class="mr-1 bg-gray-300 text-gray-800 py-2 px-4 rounded-l"
          />snmpwalk
        </div>
        <div
          class="bg-blue-500 text-white py-2 px-2 m-2 rounded focus:outline-none focus:shadow-outline"
        >
          <input
            type="checkbox"
            name="scantype"
            value="enum4linux"
            v-model="values.enum4linux"
            class="mr-1 bg-gray-300 text-gray-800 py-2 px-4 rounded-l"
          />enum4linux
        </div>
        <div
          class="bg-blue-500 text-white py-2 px-2 m-2 rounded focus:outline-none focus:shadow-outline"
        >
          <input
            type="checkbox"
            name="scantype"
            value="rdpscreenshot"
            v-model="values.rdp"
            class="mr-1 bg-gray-300 text-gray-800 py-2 px-4 rounded-l"
          />rdp
        </div>
        <div
          class="bg-blue-500 text-white py-2 px-2 m-2 rounded focus:outline-none focus:shadow-outline"
        >
          <input
            type="checkbox"
            name="scantype"
            value="webscreenshot"
            v-model="values.web"
            class="mr-1 bg-gray-300 text-gray-800 py-2 px-4 rounded-l"
          />web
        </div>
        <div
          class="bg-blue-500 text-white py-2 px-2 m-2 rounded focus:outline-none focus:shadow-outline"
        >
          <input
            type="checkbox"
            name="scantype"
            value="vncscreenshot"
            v-model="values.vnc"
            class="mr-1 bg-gray-300 text-gray-800 py-2 px-4 rounded-l"
          />VNC
        </div>
        <div
          class="bg-blue-500 text-white py-2 px-2 m-2 rounded focus:outline-none focus:shadow-outline"
        >
          <input
            type="checkbox"
            name="scantype"
            value="bluekeep"
            v-model="values.bluekeep"
            class="mr-1 bg-gray-300 text-gray-800 py-2 px-4 rounded-l"
          />Bluekeep
        </div>
        <div
          class="bg-blue-500 text-white py-2 px-2 m-2 rounded focus:outline-none focus:shadow-outline"
        >
          <input
            type="checkbox"
            name="scantype"
            value="ms17_010"
            v-model="values.ms17_010"
            class="mr-1 bg-gray-300 text-gray-800 py-2 px-4 rounded-l"
          />MS17-010
        </div>
      </div>
      <div class="mt-4 flex items-center justify-between">
        <label class="block text-gray-700 w-2/5 text-sm" for="username">target</label>
        <label class="block text-gray-700 w-1/5 text-sm" for="netmask">netmask</label>
        <label class="block text-gray-700 w-1/5 text-sm" for="port">job max mask</label>
        <label class="block text-gray-700 w-1/5 text-sm" for="port">port</label>
      </div>
      <div class="flex items-center justify-between">
        <input
          class="shadow appearance-none border rounded w-2/5 py-2 px-1 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          id="target"
          type="text"
          v-model="values.target"
          placeholder="192.168.1.1"
        />
        <input
          class="shadow appearance-none border rounded w-1/5 mx-2 py-2 px-1 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          id="netmask"
          type="text"
          v-model="values.netmask"
          placeholder="16"
        />
        <input
          class="shadow appearance-none border rounded w-1/5 mx-2 py-2 px-1 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          id="port"
          type="text"
          v-model="values.splitmask"
          placeholder="24"
        />
        <input
          class="shadow appearance-none border rounded w-1/5 mx-2 py-2 px-1 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          id="port"
          type="text"
          v-model="values.port"
          placeholder="80"
        />
      </div>
      <div class="mt-8 flex items-center justify-center">
        <input
          type="checkbox"
          name="scantype"
          value="enum4linux"
          v-model="values.onlyfound"
          class="mr-2 bg-gray-300 text-gray-800 py-2 px-4 rounded-l"
        />Only scan discovered hosts
      </div>

      <div class="mt-8 flex items-center justify-center">
        <button
          class="bg-blue-500 text-white py-2 px-4 rounded focus:outline-none focus:shadow-outline"
          type="button"
          @click="submit()"
        >Submit</button>
      </div>
    </form>
    <div v-if="scanlist.length > 0">
      <p>Nmap & masscan done so far:</p>
      <table class="table-auto">
        <tr class="odd:bg-green-200 even:bg-teal-200" v-for="scan in scanlist" :key="scan">
          <td class="p-2">{{scan['scantype']}}</td>
          <td class="p-2">{{scan['target']}}</td>
        </tr>
      </table>
    </div>
  </div>
</template>

<script>
/* eslint-disable no-console */
/* eslint-disable no-unused-vars */

import Vue from "vue";
import VueX from "vuex";
import VueRouter from "vue-router";
Vue.use(VueRouter);
Vue.use(VueX);
import axios from "axios";

export default {
  name: "Scanner",
  props: {
    scanlist: []
  },
  data() {
    return {
      values: {
        target: "",
        netmask: "",
        splitmask: "",
        port: "",
        masscan: false,
        nmap: false,
        ffuf: false,
        snmp: false,
        enum4linux: false,
        rdp: false,
        web: false,
        vnc: false,
        bluekeep: false,
        ms17_010: false,
        onlyfound: false
      }
    };
  },
  mounted() {
    this.getscans();
  },

  methods: {
    async post(url) {
      console.log("posting to " + url);
      const response = await axios.post(url);
      console.log("response:");
      console.log(response.data);
    },

    async getscans() {
      const scans = await axios.get("/api/scans/");
      console.log("scans");
      this.scanlist = scans.data["scans"];
      console.log(this.scanlist);
    },

    requestscan(scantype, targetspec, onlyfound) {
      let url = "/api/jobs/?type=" + scantype + targetspec;
      if (onlyfound) {
        url += "&found_only=true";
      } else {
        url += "&found_only=false";
      }
      this.post(url);
    },
    submit() {
      if (this.values.target.length == 0) {
        alert("target field is empty, idiot");
        return;
      }
      const netmask =
        this.values.netmask.length > 0 ? this.values.netmask : "32";

      let targetspec = "&target=" + this.values.target + "&mask=" + netmask;
      if (this.values.port.length > 0) {
        targetspec += "&port=" + this.values.port;
      }
      if (this.values.splitmask.length > 0) {
        targetspec += "&maxmask=" + this.values.splitmask;
      }

      // curl -X POST 'http://localhost:8888/jobs/?prefix=10.20.20.85&type=snmpwalk'
      if (this.values.masscan) {
        this.requestscan("masscan", targetspec, false);
        this.values.masscan = false;
      }
      if (this.values.nmap) {
        this.requestscan("nmap", targetspec, this.values.onlyfound);
        this.values.nmap = false;
      }
      if (this.values.web) {
        this.requestscan("webscreenshot", targetspec, this.values.onlyfound);
        this.values.web = false;
      }
      if (this.values.rdp) {
        this.requestscan("rdpscreenshot", targetspec, this.values.onlyfound);
        this.values.rdp = false;
      }
      if (this.values.vnc) {
        this.requestscan("vncscreenshot", targetspec, this.values.onlyfound);
        this.values.vnc = false;
      }
      if (this.values.snmp) {
        this.requestscan("snmpwalk", targetspec, this.values.onlyfound);
        this.values.snmp = false;
      }
      if (this.values.enum4linux) {
        this.requestscan("enum4linux", targetspec, this.values.onlyfound);
        this.values.enum4linux = false;
      }
      if (this.values.ffuf) {
        this.requestscan("ffuf", targetspec, this.values.onlyfound);
        this.values.ffuf = false;
      }
      if (this.values.bluekeep) {
        this.requestscan("bluekeep", targetspec, this.values.onlyfound);
        this.values.bluekeep = false;
      }
      if (this.values.ms17_010) {
        this.requestscan("ms17_010", targetspec, this.values.onlyfound);
        this.values.ms17_010 = false;
      }
    }
  }
};
</script>