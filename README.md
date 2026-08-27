![OpenWrt logo](include/logo.png)

OpenWrt Project is a Linux operating system targeting embedded devices. Instead
of trying to create a single, static firmware, OpenWrt provides a fully
writable filesystem with package management. This frees you from the
application selection and configuration provided by the vendor and allows you
to customize the device through the use of packages to suit any application.
For developers, OpenWrt is the framework to build an application without having
to build a complete firmware around it; for users this means the ability for
full customization, to use the device in ways never envisioned.

Sunshine!

## QCN5502 Fork Features (2.4 GHz Wi-Fi Support)

This repository is an OpenWrt fork with experimental support for the **Qualcomm QCN5502** SoC (`ath9k`), enabling fully functional **2.4 GHz wireless** alongside the 5 GHz radio (`ath10k`).

### Supported QCN5502 Devices:
- **TP-Link Archer A9 v6** (`ath79/generic/tplink_archer-a9-v6`)
- **ASUS RT-AC59U v2** (`ath79/generic/asus_rt-ac59u-v2`) — *also covers RT-AC1300G PLUS v3, RT-AC57U v3, RT-AC58U v3*
- **ASUS RT-AC59U** (`ath79/generic/asus_rt-ac59u`) — *also covers RT-AC1200GE, RT-AC1500G PLUS, RT-AC1500UHP, RT-AC57U v2, RT-AC58U v2, RT-ACRH12*
- **ASUS ZenWiFi AC Mini (CD6)** (`ath79/generic/asus_zenwifi-cd6n` & `asus_zenwifi-cd6r`)
- **NETGEAR EX7300 v2** (`ath79/generic/netgear_ex7300-v2`) — *also covers EX6250, EX6400 v2, EX6410, EX6420, EX7320*

---

## Automated Firmware Building (GitHub Actions)

You can build custom firmware directly on GitHub without setting up a local Linux build environment.

### How to Build Firmware:
1. Navigate to the **Actions** tab in this GitHub repository.
2. Select the **Build OpenWrt Firmware** workflow in the left sidebar.
3. Click **Run workflow** on the right side.
4. Configure the inputs:
   - **Router Model**: Choose your router from the dropdown (e.g. `TP-Link Archer A9 v6`), or select `Custom (specify in custom_router_model)`.
   - **Custom Router Model**: *(Optional)* Enter any other router model supported by OpenWrt (e.g. `GL-MT3000`, `x86/64`, `ath79/generic/tplink_archer-c7-v5`).
   - **Packages**: Enter any custom packages to include, separated by spaces or newlines:
     ```text
     luci
     luci-app-firewall
     kmod-usb2
     ```
   - **Create Release**: Keep checked to automatically publish a GitHub Release with attached firmware binaries, SHA256 checksums, and release notes.
5. Click **Run workflow**.

### Downloading Firmware:
- **GitHub Releases**: If *Create Release* is enabled, visit the repository's **Releases** page to download the factory and sysupgrade images along with SHA256 checksums.
- **Workflow Run Artifacts**: Download the `openwrt-<router>-<date>` ZIP bundle directly from the completed workflow run summary page.

---

## Download

##

An advanced user may require additional or specific package. (Toolchain, SDK, ...) For everything else than simple firmware download, try the wiki download page:

* [OpenWrt Wiki Download](https://openwrt.org/downloads)

## Development

To build your own firmware you need a GNU/Linux, BSD or macOS system (case
sensitive filesystem required). Cygwin is unsupported because of the lack of a
case sensitive file system.

### Requirements

You need the following tools to compile OpenWrt, the package names vary between
distributions. A complete list with distribution specific packages is found in
the [Build System Setup](https://openwrt.org/docs/guide-developer/build-system/install-buildsystem)
documentation.

```
binutils bzip2 diff find flex gawk gcc-6+ getopt grep install libc-dev libz-dev
make4.1+ perl python3.8+ rsync subversion unzip which
```

### Quickstart

1. Run `./scripts/feeds update -a` to obtain all the latest package definitions
   defined in feeds.conf / feeds.conf.default

2. Run `./scripts/feeds install -a` to install symlinks for all obtained
   packages into package/feeds/

3. Run `make menuconfig` to select your preferred configuration for the
   toolchain, target system & firmware packages.

4. Run `make` to build your firmware. This will download all sources, build the
   cross-compile toolchain and then cross-compile the GNU/Linux kernel & all chosen
   applications for your target system.

### Related Repositories

The main repository uses multiple sub-repositories to manage packages of
different categories. All packages are installed via the OpenWrt package
manager called `opkg`. If you're looking to develop the web interface or port
packages to OpenWrt, please find the fitting repository below.

* [LuCI Web Interface](https://github.com/openwrt/luci): Modern and modular
  interface to control the device via a web browser.

* [OpenWrt Packages](https://github.com/openwrt/packages): Community repository
  of ported packages.

* [OpenWrt Routing](https://github.com/openwrt/routing): Packages specifically
  focused on (mesh) routing.

* [OpenWrt Video](https://github.com/openwrt/video): Packages specifically
  focused on display servers and clients (Xorg and Wayland).

## Support Information

For a list of supported devices see the [OpenWrt Hardware Database](https://openwrt.org/supported_devices)

### Documentation

* [Quick Start Guide](https://openwrt.org/docs/guide-quick-start/start)
* [User Guide](https://openwrt.org/docs/guide-user/start)
* [Developer Documentation](https://openwrt.org/docs/guide-developer/start)
* [Technical Reference](https://openwrt.org/docs/techref/start)

### Support Community

* [Forum](https://forum.openwrt.org): For usage, projects, discussions and hardware advise.
* [Support Chat](https://webchat.oftc.net/#openwrt): Channel `#openwrt` on **oftc.net**.

### Developer Community

* [Bug Reports](https://bugs.openwrt.org): Report bugs in OpenWrt
* [Dev Mailing List](https://lists.openwrt.org/mailman/listinfo/openwrt-devel): Send patches
* [Dev Chat](https://webchat.oftc.net/#openwrt-devel): Channel `#openwrt-devel` on **oftc.net**.

## License

OpenWrt is licensed under GPL-2.0
