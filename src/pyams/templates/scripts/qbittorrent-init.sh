#!/bin/bash
(
  # qBittorrent config is typically in qBittorrent.conf
  CONFIG_FILE="/config/qBittorrent/qBittorrent.conf"

  # For LinuxServer.io, wait for first run to generate config
  while [ ! -f "$CONFIG_FILE" ]; do sleep 2; done

  echo "qBittorrent config found! Applying PYAMS defaults..."

  # Helper function to set or update a key
  set_config() {
    local key="$1"
    local value="$2"
    # Escape backslashes in key for sed regex
    local escaped_key="${key//\\/\\\\}"
    if grep -q "^${escaped_key}=" "$CONFIG_FILE"; then
      # Use @ as delimiter for sed to avoid issues with slashes in value
      sed -i "s@^${escaped_key}=.*@${key}=${value}@" "$CONFIG_FILE"
    else
      # Ensure [Preferences] exists, if not append it
      if ! grep -q "^\[Preferences\]" "$CONFIG_FILE"; then
        echo "[Preferences]" >>"$CONFIG_FILE"
      fi
      # Append under [Preferences] section
      sed -i "/^\[Preferences\]/a ${key}=${value}" "$CONFIG_FILE"
    fi
  }

  # 3. Downloads Configuration
  set_config 'Session\\DefaultSavePath' '/data/downloads/torrents'

  # 4. BitTorrent (Seeding) Settings - Stop seeding when ratio reaches 0
  set_config 'Bittorrent\\MaxRatioAction' '0'
  set_config 'Bittorrent\\MaxRatio' '0'

  # 4.5. Excluded File Names
  set_config 'Session\\ExcludedFileNamesEnabled' 'true'
  set_config 'Session\\ExcludedFileNames' '"*.apk;*.bin;*.dll;*.exe;*.msi;*.txt;*.url;*.001;*.7z;*.7z*;*.arj;*.arj*;*.b1;*.b1*;*.b6z*;*.b6z;*.bh*;*.bh*;*.br*;*.br;*.bz2*;*.bz2;*.cab*;*.cab;*.dar*;*.dar;*.dmg*;*.dmg;*.gz*;*.gz;*.ha*;*.ha;*.ice*;*.ice;*.ipa*;*.ipa;*.iso*;*.iso;*.kgb*;*.kgb;*.lz*;*.lz;*.partimg*;*.partimg;*.rar*;*.rar;*.sda*;*.sda;*.sea*;*.sea;*.st*;*.st;*.tar*;*.tar;*.tbz2*;*.tbz2;*.tgz*;*.tgz;*.tlz;*.tlz;*.txz*;*.txz;*.wim*;*.wim;*.xz*;*.xz;*.z*;*.z;*.zip*;*.zip;*.zipx*;*.zipx;*.zpaq*;*.zpaq;*.zst*;*.zst;*.zz*;*.zz;*.accda;*.accdb;*.accdc;*.accde;*.accdr;*.accdt;*.accdu;*.cfg;*.conf;*.csv;*.doc;*.docm;*.docx;*.dotm;*.dotx;*.duarcfg;*.ecf;*.env;*.eps;*.hta;*.html;*.ini;*.inf;*.info;*.inx;*.job;*.json;*.jtrrcfg;*.md;*.netcfg;*.netccfg;*.netecfg;*.netgcfg;*.ods;*.one;*.pdf;*.php;*.pot;*.potm;*.potx;*.ppa;*.ppam;*.pps;*.ppsm;*.ppsx;*.ppt;*.pptm;*.pptx;*.properties;*.prx;*.prxe;*.ps;*.pub;*.puff;*.rc;*.reg;*.rtf;*.sldm;*.sldx;*.sumocfg;*.toml;*.wbk;*.xaml;*.xlam;*.xls;*.xlsb;*.xlsm;*.xlsx;*.xlm;*.xlt;*.xltm;*.xltx;*.xml;*.xsd;*.yaml;*.yml;*.4DB;*.4DC;*.4DD;*.BSON;*.CDB;*.CRYPT1;*.CRYPT10;*.CRYPT5;*.CRYPT6;*.CRYPT7;*.CRYPT8;*.CRYPT9;*.DBC;*.DB;*.DB-JOURNAL;*.DB-WAL;*.DDL;*.FMP12;*.FMPSL;*.FP3;*.FP7;*.GDB;*.MARSHAL;*.MDB;*.MDF;*.NDF;*.NSF;*.ODB;*.PDB;*.SDF;*.SQLITE;*.SQLITEDB;*.SQLITE3;*.TRC;*.UDL;*.appx;*.appxbundle;*.axf;*.bat;*.cmd;*.deb;*.elf;*.ex;*.ins;*.isu;*.jar;*.js;*.jsx;*.jse;*.j;*.ko;*.lnk;*.mpkg;*.msix;*.mod;*.out;*.o;*.obs;*.pkg;*.ps1;*.py;*.pyc;*.pyo;*.rpm;*.run;*.scr;*.script;*.sh;*.so;*.vb;*.vbs;*.ws;*.wsf;*.wsh;*.0XE;*.73K;*.89K;*.A6P;*.AC;*.ACC;*.ACR;*.ACTM;*.AHK;*.AIR;*.APP;*.ARSCRIPT;*.AS;*.ASB;*.AWK;*.AZW2;*.BEAM;*.BTM;*.BUP;*.CAB;*.CEL;*.CELX;*.CHM;*.COF;*.COM;*.CRT;*.DEK;*.DLD;*.DMC;*.DXL;*.EAR;*.EBM;*.EBS;*.EBS2;*.ECF;*.EHAM;*.ES;*.EX4;*.EXM;*.EXP;*.EXOPC;*.EZS;*.FAS;*.FKY;*.FPI;*.FRS;*.FXP;*.GEO;*.GS;*.HAM;*.HMS;*.HPF;*.IFO;*.IIM;*.IPF;*.KIX;*.LO;*.LS;*.MAM;*.MCR;*.MEL;*.MPX;*.MRC;*.MS;*.MSP;*.MXE;*.NEXE;*.OCX;*.ORE;*.OTM;*.PEX;*.PIM;*.PLX;*.PRC;*.PVD;*.PWC;*.QPX;*.RBX;*.ROX;*.RPJ;*.S2A;*.SBS;*.SCA;*.SCAR;*.SCB;*.SPR;*.TCP;*.THM;*.TLB;*.TMX;*.UDF;*.UPX;*.VLX;*.VPM;*.WCM;*.WEBSITE;*.WIDGET;*.WIZ;*.WPK;*.WPM;*.XAP;*.XBAP;*.XIP;*.XQT;*.XYS;*.ZL9;*(sample).*"'

  # 5. Web UI & Security - Bypass authentication for clients on local network
  set_config 'WebUI\\AuthSubnetWhitelistEnabled' 'true'
  set_config 'WebUI\\AuthSubnetWhitelist' '10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16'

  # Set default Web UI password to match Sonarr download client config
  set_config 'WebUI\\Password_PBKDF2' '"@ByteArray(MWViRZ1HBy0ZgU22B1pf9A==:+bZW8kQeJhGoxnVYCC/QRot6VNid1fKlGAA9o8XaqDnUtY7vjcEdGkST3Q0WADES0Dns3/YlKRINfRk5PmWGYQ==)"'

  # 6. Network Binding
  if [ "${USE_VPN:-false}" = "true" ]; then
    echo "VPN enabled, binding qBittorrent to tun0 interface..."
    set_config 'Connection\\Interface' 'tun0'
    set_config 'Connection\\InterfaceName' 'tun0'
  else
    echo "VPN disabled, no specific interface binding applied."
    # If the user disabled VPN later, we might want to unset these or bind to any
    # But usually it's fine to leave it as is if it's the default, or explicitly unset
  fi

  echo "qBittorrent configuration applied."
) &
