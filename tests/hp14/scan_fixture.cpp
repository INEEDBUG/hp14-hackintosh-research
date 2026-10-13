// SPDX-License-Identifier: GPL-2.0-only
// Copyright (C) 2026 INEEDBUG. Host fixtures use fictional network data.
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstdlib>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#include <mutex>
#include <string>
#include <sys/tree.h>
#include <vector>

using IOReturn = int;
using OSObject = void;
constexpr int kIOReturnSuccess = 0, kIOReturnBadArgument = -2;
constexpr int kIOReturnNotReady = -3, kIOReturnUnsupported = -4;
constexpr int IEEE80211_S_INIT = 0, IEEE80211_S_SCAN = 1, IEEE80211_S_RUN = 4;
constexpr int IEEE80211_F_BGSCAN = 1, IEEE80211_F_ASCAN = 2;
constexpr unsigned APPLE80211_SCAN_TYPE_FAST = 2, APPLE80211_SCAN_TYPE_PASSIVE = 3;
constexpr unsigned APPLE80211_VERSION = 1;
constexpr unsigned IEEE80211_ADDR_LEN = 6;
constexpr int IWM_MIN_DBM = -100;
#define XYLog(...) ((void)0)
#define MIN(a,b) ((a) < (b) ? (a) : (b))
inline void bzero(void *p, size_t n) { std::memset(p, 0, n); }

struct ieee80211_channel { unsigned number = 36, ic_flags = 0; };
struct ieee80211_node {
    RB_ENTRY(ieee80211_node) entry;
    uint8_t ni_macaddr[6] {}, ni_bssid[6] {}, ni_essid[32] {};
    unsigned ni_esslen = 0;
    struct { unsigned rs_nrates = 0; uint8_t rs_rates[16] {}; } ni_rates;
    uint8_t *ni_rsnie_tlv = nullptr;
    unsigned ni_rsnie_tlv_len = 0, ni_intval = 100, ni_age_ts = 0, ni_capinfo = 0;
    int ni_rssi = 67;
    ieee80211_channel *ni_chan = nullptr;
};
RB_HEAD(ieee80211_tree, ieee80211_node);
static int compareNodes(ieee80211_node *a, ieee80211_node *b) {
    return std::memcmp(a->ni_macaddr, b->ni_macaddr, 6);
}
RB_PROTOTYPE_STATIC(ieee80211_tree, ieee80211_node, entry, compareNodes)
RB_GENERATE_STATIC(ieee80211_tree, ieee80211_node, entry, compareNodes)
struct ieee80211com {
    int ic_state = IEEE80211_S_RUN;
    unsigned ic_flags = 0;
    ieee80211_tree ic_tree {};
    struct { int ac_if; } ic_ac {};
};
struct apple80211_scan_data { unsigned scan_type = 0; };
struct apple80211_scan_result {
    unsigned version, asr_ie_len, asr_beacon_int, asr_nrates;
    uint8_t asr_ie_data[256], asr_rates[16];
    unsigned asr_age, asr_cap;
    struct { unsigned version, channel, flags; } asr_channel;
    int asr_noise, asr_rssi;
    uint8_t asr_bssid[6]; unsigned asr_ssid_len; uint8_t asr_ssid[32];
};
struct Timer {
    unsigned delay = 0, calls = 0;
    void setTimeoutMS(unsigned ms) { delay = ms; ++calls; }
    void enable() {}
};
struct Info { int getBSSNoise() { return 0; } };
struct Hal {
    ieee80211com ic; Info info;
    ieee80211com *get80211Controller() { return &ic; }
    Info *getDriverInfo() { return &info; }
};
using ItlHalService = Hal;
static bool insideGate = false;
static std::vector<std::string> diagnosticLines;
static void IOLog(const char *format, ...) {
    char message[512]; va_list args; va_start(args,format);
    std::vsnprintf(message,sizeof(message),format,args); va_end(args);
    diagnosticLines.emplace_back(message);
}
struct WorkLoop { bool inGate() { return insideGate; } };
struct IOCommandGate {
    using Action = IOReturn (*)(OSObject *, void *, void *, void *, void *);
    std::recursive_mutex mutex;
    WorkLoop loop;
    WorkLoop *getWorkLoop() { return &loop; }
    IOReturn runAction(Action action, void *a0=nullptr, void *a1=nullptr,
                       void *a2=nullptr, void *a3=nullptr) {
        std::lock_guard<std::recursive_mutex> lock(mutex);
        bool old = insideGate; insideGate = true;
        IOReturn result = action(nullptr,a0,a1,a2,a3); insideGate = old;
        return result;
    }
};
static IOCommandGate gate;
static IOCommandGate *_fCommandGate = &gate;
static unsigned bgscanCalls = 0;
static void ieee80211_begin_cache_bgscan(int *) { ++bgscanCalls; }
static unsigned ieee80211_chan2ieee(ieee80211com *, ieee80211_channel *c) { return c->number; }
static unsigned ieeeChanFlag2appleScanFlagVentura(unsigned) { return 0; }
static unsigned airport_up_time() { return 1; }
static void ieee80211_free_allnodes(ieee80211com *ic, int) {
    while (auto n=RB_MIN(ieee80211_tree,&ic->ic_tree)) {
        RB_REMOVE(ieee80211_tree,&ic->ic_tree,n); delete n;
    }
}
struct AirportItlwmSkywalkInterface {
    Hal hal; Timer timer;
    Hal *fHalService = &hal;
    Timer *scanSource = &timer;
    ieee80211_node *fNextNodeToSend = nullptr;
    bool fScanResultWrapping = false, wclStopping = false;
    uint8_t scanCursorMAC[6] {};
    bool scanCursorValid = false;
    bool scanPending=false, joinPending=false, joinDeferred=false, portAuthorized=false;
    uint64_t wifiDiagnosticSequence=0;
    uint32_t wifiDiagnosticStageCount[32] {};
    void recordWiFiDiagnostic(unsigned,IOReturn,unsigned detail=0);
    IOReturn setSCAN_REQ(apple80211_scan_data *);
    IOReturn getSCAN_RESULT(apple80211_scan_result *);
    IOReturn setSCANCACHE_CLEAR(void *);
    IOReturn setSCAN_REQGated(apple80211_scan_data *);
    IOReturn getSCAN_RESULTGated(apple80211_scan_result *);
    IOReturn clearSCANCACHEGated();
    void resetScanCursor();
    static IOReturn scanCursorCommand(OSObject *,void *,void *,void *,void *);
};

#include "production.inc"

static ieee80211_channel channel;
static ieee80211_node *add(AirportItlwmSkywalkInterface &driver, uint8_t key) {
    auto n = new ieee80211_node;
    n->ni_macaddr[0] = n->ni_bssid[0] = 2;
    n->ni_macaddr[5] = n->ni_bssid[5] = key;
    n->ni_essid[0] = 'T'; n->ni_esslen = 1; n->ni_chan = &channel;
    n->ni_rates.rs_nrates = 2; n->ni_rates.rs_rates[0] = 12; n->ni_rates.rs_rates[1] = 24;
    assert(!RB_INSERT(ieee80211_tree,&driver.hal.ic.ic_tree,n)); return n;
}
static void check(bool condition,const char *message) {
    if (!condition) { std::fprintf(stderr,"FAIL %s\n",message); std::exit(1); }
}
static void run(const char *test) {
    AirportItlwmSkywalkInterface d;
    apple80211_scan_data req {}; apple80211_scan_result result {};
    if (!std::strcmp(test,"restart_after_last_result")) {
        add(d,10);
        check(d.getSCAN_RESULT(&result)==0,"first result available");
        check(d.setSCAN_REQ(&req)==0,"new scan after last result must be accepted");
        check(d.getSCAN_RESULT(&result)==0 && result.asr_bssid[5]==10,"new scan starts at first BSS");
    } else if (!std::strcmp(test,"restart_after_partial_read")) {
        add(d,10);add(d,20);add(d,30);
        check(d.getSCAN_RESULT(&result)==0 && result.asr_bssid[5]==10,"first BSS");
        check(d.setSCAN_REQ(&req)==0,"new scan accepted after partial read");
        check(d.getSCAN_RESULT(&result)==0 && result.asr_bssid[5]==10,"partial old cursor must not omit first BSS");
    } else if (!std::strcmp(test,"cache_freed_between_reads")) {
        add(d,10);add(d,20);
        check(d.getSCAN_RESULT(&result)==0,"first result available before cache clear");
        ieee80211_free_allnodes(&d.hal.ic,0);add(d,30);
        check(d.getSCAN_RESULT(&result)==0 && result.asr_bssid[5]==30,"read live replacement tree without dereferencing freed cursor");
    } else if (!std::strcmp(test,"cache_clear_starts_new_enumeration")) {
        add(d,10);add(d,20);
        check(d.getSCAN_RESULT(&result)==0,"first result available");
        check(d.setSCANCACHE_CLEAR(nullptr)==0,"cache clear succeeds");add(d,5);
        check(d.getSCAN_RESULT(&result)==0 && result.asr_bssid[5]==5,"explicit cache clear invalidates old enumeration");
    } else if (!std::strcmp(test,"rates_are_copied")) {
        add(d,10);check(d.getSCAN_RESULT(&result)==0,"result available");
        check(result.asr_nrates==2 && result.asr_rates[0]==12 && result.asr_rates[1]==24,"nonzero advertised rate count must have populated rates");
    } else if (!std::strcmp(test,"init_rejection_preserved")) {
        d.hal.ic.ic_state=IEEE80211_S_INIT;
        check(d.setSCAN_REQ(&req)==22,"INIT remains unavailable, not fabricated success");
    } else if (!std::strcmp(test,"complete_list_and_eof")) {
        add(d,10);add(d,20);add(d,30);
        for(unsigned key:{10U,20U,30U})
            check(d.getSCAN_RESULT(&result)==0 && result.asr_bssid[5]==key,"ordered complete enumeration");
        check(d.getSCAN_RESULT(&result)==5,"EOF retained");
    } else if (!std::strcmp(test,"passive_scan_does_not_start_active_bgscan")) {
        req.scan_type=APPLE80211_SCAN_TYPE_PASSIVE;bgscanCalls=0;
        check(d.setSCAN_REQ(&req)==0 && bgscanCalls==0,"passive request never upgraded to active scan");
    } else if (!std::strcmp(test,"scan_request_emits_numeric_diagnostic")) {
        diagnosticLines.clear();check(d.setSCAN_REQ(&req)==0,"scan accepted");
        check(diagnosticLines.size()==1,"one numeric diagnostic emitted for accepted request");
        check(diagnosticLines[0].find("HP14WIFI v1 ")==0 &&
              diagnosticLines[0].find("stage=1 ")!=std::string::npos &&
              diagnosticLines[0].find("status=00000000 ")!=std::string::npos,
              "diagnostic identifies real callback and return status");
        check(diagnosticLines[0].find("ssid")==std::string::npos &&
              diagnosticLines[0].find("bssid")==std::string::npos &&
              diagnosticLines[0].find("password")==std::string::npos,
              "numeric diagnostic contains no network identity or credential fields");
    } else if (!std::strcmp(test,"diagnostic_is_line_delimited")) {
        diagnosticLines.clear();check(d.setSCAN_REQ(&req)==0,"request accepted");
        check(!diagnosticLines.empty() && diagnosticLines[0].back()=='\n',"diagnostics must be line delimited");
    } else if (!std::strcmp(test,"rate_count_is_bounded")) {
        auto n=add(d,10);n->ni_rates.rs_nrates=255;
        check(d.getSCAN_RESULT(&result)==0 && result.asr_nrates==16,"malformed rate count remains bounded");
    } else if (!std::strcmp(test,"unavailable_gate_is_rejected")) {
        _fCommandGate=nullptr;
        check(d.setSCAN_REQ(&req)==kIOReturnNotReady && d.getSCAN_RESULT(&result)==kIOReturnNotReady,
              "unavailable command gate returns failure");_fCommandGate=&gate;
    } else if (!std::strcmp(test,"stopping_is_rejected")) {
        d.wclStopping=true;
        check(d.setSCAN_REQ(&req)==kIOReturnNotReady && d.getSCAN_RESULT(&result)==kIOReturnNotReady,
              "stopping interface rejects new work");
    } else if (!std::strcmp(test,"active_scan_preserves_cache")) {
        add(d,10);d.hal.ic.ic_flags=IEEE80211_F_ASCAN;
        check(d.setSCANCACHE_CLEAR(nullptr)==0 && RB_MIN(ieee80211_tree,&d.hal.ic.ic_tree)!=nullptr,
              "active scan cache is not freed by clear");
    } else { check(false,"unknown test"); }
    ieee80211_free_allnodes(&d.hal.ic,0);
    std::printf("PASS %s\n",test);
}
int main(int argc,char **argv) { if(argc!=2)return 2;run(argv[1]); }
