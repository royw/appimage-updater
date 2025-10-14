<!-- markdownlint-disable MD033 -->

# AppImage Updater

[![CI/CD](https://github.com/royw/appimage-updater/actions/workflows/ci.yml/badge.svg)](https://github.com/royw/appimage-updater/actions/workflows/ci.yml)
[![Documentation](https://github.com/royw/appimage-updater/actions/workflows/docs.yml/badge.svg)](https://github.com/royw/appimage-updater/actions/workflows/docs.yml)
[![Docs Site](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://royw.github.io/appimage-updater/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Linux service for automating updates of AppImage applications from their respective websites.

## Overview

AppImage Updater monitors configured applications for new releases and provides automated downloading of updated AppImage files.

**Platform Support**: Linux only - AppImage is a Linux-specific package format. See [Linux-Only Support](https://royw.github.io/appimage-updater/linux-only/) for details.

**Key Features:**

- **High Performance**: Async operations with concurrent downloads and parallel processing
- **Multi-Format Output**: Rich terminal UI, plain text, JSON, and HTML output formats
- **Multi-Repository Support**: GitHub releases, direct downloads, and dynamic URLs

**Supported Sources:**

- **GitHub** releases with intelligent asset selection and API integration
- **GitLab** repositories (gitlab.com and self-hosted) with GitLab API v4 support
- **Codeberg** and other GitHub-compatible Git forges (Gitea, Forgejo)
- **Direct download URLs** with checksum verification and automatic detection
- **Dynamic URLs** with automatic resolution and fallback support
- **ZIP files** containing AppImage files with automatic extraction
- **Multi-architecture releases** with automatic compatibility detection (x86_64, arm64, etc.)

## Requirements

- Python 3.11 or higher
- pipx (for recommended installation) or pip

## Installation

**Recommended (pipx):**

```bash
pipx install appimage-updater
```

**Alternative methods:**

```bash
# User pip install
pip install --user appimage-updater

# Executing from source
git clone https://github.com/royw/appimage-updater.git
cd appimage-updater
uv sync
uv run appimage-updater --help
```

For detailed installation instructions and troubleshooting, see the [Installation Guide](https://royw.github.io/appimage-updater/installation/).

## Quick Start

```bash
# Add applications from different repository types
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD
appimage-updater add Inkscape https://gitlab.com/inkscape/inkscape ~/Applications/Inkscape
appimage-updater add OpenRGB https://codeberg.org/OpenRGB/OpenRGB ~/Applications/OpenRGB

# Filter versions with patterns (exclude prereleases)
appimage-updater add --version-pattern "^[0-9]+\.[0-9]+$" MyApp https://github.com/user/repo ~/Apps/MyApp

# Check for updates
appimage-updater check

# List configured applications
appimage-updater list

# Use different output formats (rich, plain, json, html)
appimage-updater list --format json  # List all configured apps as a JSON
appimage-updater check --format plain  # Check for updates and show plain text output
appimage-updater show MyApp --format html  # Show app details in HTML format

# Help is available:
appimage-updater --help
appimage-updater list --help
appimage-updater add --help
appimage-updater edit --help
appimage-updater show --help
appimage-updater check --help
appimage-updater remove --help
appimage-updater config --help
```

## Example

For example, you want to keep current official releases and weekly releases of
[FreeCAD](https://github.com/FreeCAD/FreeCAD). You use [appimaged](https://github.com/probonopd/go-appimage) to
integrate your AppImages into your system. You do not want the official releases integrated into your system (i.e.,
you are ok with manually running them from the terminal) so you do not want them on appimaged's search path. However
you do want the latest weekly release integrated into your system, and a few previous releases if you need to track
down a development issue.

Official Releases go into ~/Applications/FreeCAD/ while the weekly releases go into ~/Applications/FreeCAD_weekly/.
A symbolic link, ~/Applications/FreeCAD_weekly.AppImage is on appimaged's search path and points to the current
weekly release. If you hit an issue with the current release, simply replace the symbolic link with one that
points to an old release.

Cool. Works nicely except you have to manually check the github repository, download updates, verify checksums,
and rotate the extensions and symbolic link. This is where appimage-updater comes in.

Here is an example of FreeCAD AppImages that appimage-updater is currently managing:

```bash
➤ tree -l -P "[fF]r*" -I "[a-eA-Eg-zG-z]*" -C ~/Applications
```

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">

<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title></title>
<style type="text/css">
.ansi2html-content { display: inline; white-space: pre-wrap; word-wrap: break-word; }
.body_foreground { color: #AAAAAA; }
.body_background { background-color: #000000; }
.inv_foreground { color: #000000; }
.inv_background { background-color: #AAAAAA; }
.ansi1 { font-weight: bold; }
.ansi31 { color: #aa0000; }
.ansi32 { color: #00aa00; }
.ansi36 { color: #00aaaa; }
</style>
</head>
<body class="body_foreground body_background">
<pre class="ansi2html-content"  style="font-size: 70%;" >
<span class="ansi1 ansi31"></span>
├── <span class="ansi1 ansi31">FreeCAD</span>
│   ├── <span class="ansi1 ansi32">FreeCAD-1.0.0-conda-Linux-x86_64-py311.appimage</span>
│   ├── <span class="ansi1 ansi32">FreeCAD_1.0.2-conda-Linux-x86_64-py311.AppImage</span>
│   └── FreeCAD_1.0.2-conda-Linux-x86_64-py311.AppImage.info
├── FreeCAD.readme
├── <span class="ansi1 ansi31">FreeCAD_weekly</span>
│   ├── <span class="ansi1 ansi32">FreeCAD_weekly-2025.09.11-Linux-x86_64-py311.AppImage.old</span>
│   ├── FreeCAD_weekly-2025.09.11-Linux-x86_64-py311.AppImage.old.info
│   ├── <span class="ansi1 ansi32">FreeCAD_weekly-2025.09.12-Linux-x86_64-py311.AppImage.old</span>
│   ├── FreeCAD_weekly-2025.09.12-Linux-x86_64-py311.AppImage.old.info
│   ├── <span class="ansi1 ansi32">FreeCAD_weekly-2025.09.24-Linux-x86_64-py311.AppImage.old</span>
│   ├── FreeCAD_weekly-2025.09.24-Linux-x86_64-py311.AppImage.old.info
│   ├── <span class="ansi1 ansi32">FreeCAD_weekly-2025.10.01-Linux-x86_64-py311.AppImage.old</span>
│   ├── FreeCAD_weekly-2025.10.01-Linux-x86_64-py311.AppImage.old.info
│   ├── <span class="ansi1 ansi32">FreeCAD_weekly-2025.10.08-Linux-x86_64-py311.AppImage.current</span>
│   └── FreeCAD_weekly-2025.10.08-Linux-x86_64-py311.AppImage.current.info
└── <span class="ansi1 ansi36">FreeCAD_weekly.AppImage</span> -&gt; <span class="ansi1 ansi32">/home/royw/Applications/FreeCAD_weekly/FreeCAD_weekly-2025.10.08-Linux-x86_64-py311.AppImage.current</span>

3 directories, 15 files

</pre>
</body>

</html>

Add FreeCAD official releases:

```bash
➤ appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD/releases ~/Applications/FreeCAD
Detected download URL, using repository URL instead:
   Original: https://github.com/FreeCAD/FreeCAD/releases
   Corrected: https://github.com/FreeCAD/FreeCAD
Successfully added application 'FreeCAD'
Source: https://github.com/FreeCAD/FreeCAD
Download Directory: /home/royw/Applications/FreeCAD
Pattern: (?i)FreeCAD.*\.(zip|AppImage)(\.(|current|old))?$

Tip: Use 'appimage-updater show FreeCAD' to view full configuration
```

Notice that the URL is corrected from the release directory (could even be the image file itself), to the project directory.

Add FreeCAD weekly releases:

```bash
~/Applications $ appimage-updater add FreeCAD_weekly https://github.com/FreeCAD/FreeCAD/releases ~/Applications/FreeCAD_weekly --prerelease --rotation --symlink ~/Applications/FreeCAD_weekly.AppImage
Detected download URL, using repository URL instead:
   Original: https://github.com/FreeCAD/FreeCAD/releases
   Corrected: https://github.com/FreeCAD/FreeCAD
Successfully added application 'FreeCAD_weekly'
Source: https://github.com/FreeCAD/FreeCAD
Download Directory: /home/royw/Applications/FreeCAD_weekly
Pattern: (?i)FreeCAD.*\.(zip|AppImage)(\.(|current|old))?$

Tip: Use 'appimage-updater show FreeCAD_weekly' to view full configuration
```

```bash
➤ appimage-updater show FreeCAD
```

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title></title>
<style type="text/css">
.ansi2html-content { display: inline; white-space: pre-wrap; word-wrap: break-word; }
.body_foreground { color: #AAAAAA; }
.body_background { background-color: #000000; }
.inv_foreground { color: #000000; }
.inv_background { background-color: #AAAAAA; }
.ansi1 { font-weight: bold; }
.ansi2 { font-weight: lighter; }
.ansi32 { color: #00aa00; }
.ansi33 { color: #aa5500; }
.ansi34 { color: #0000aa; }
.ansi36 { color: #00aaaa; }
</style>
</head>
<body class="body_foreground body_background" >
<pre class="ansi2html-content" style="font-size: 70%;" >

<span class="ansi1 ansi36">Application: FreeCAD</span>
=====================
<span class="ansi34">╭─</span><span class="ansi34">───────────────────────────────────────</span><span class="ansi34"> Configuration </span><span class="ansi34">────────────────────────────────────────</span><span class="ansi34">─╮</span>
<span class="ansi34">│</span> <span class="ansi1">Name:</span> FreeCAD                                                                                  <span class="ansi34">│</span>
<span class="ansi34">│</span> <span class="ansi1">Status:</span> <span class="ansi32">Enabled</span>                                                                                <span class="ansi34">│</span>
<span class="ansi34">│</span> <span class="ansi1">Source:</span> Github                                                                                 <span class="ansi34">│</span>
<span class="ansi34">│</span> <span class="ansi1">URL:</span> https://github.com/FreeCAD/FreeCAD                                                        <span class="ansi34">│</span>
<span class="ansi34">│</span> <span class="ansi1">Download Directory:</span> ~/Applications/FreeCAD                                                     <span class="ansi34">│</span>
<span class="ansi34">│</span> <span class="ansi1">File Pattern:</span> (?i)FreeCAD.*\.(zip|AppImage)(\.(|current|old))?$                                <span class="ansi34">│</span>
<span class="ansi34">│</span> <span class="ansi1">Config File:</span> ~/.config/appimage-updater/apps/FreeCAD.json                                      <span class="ansi34">│</span>
<span class="ansi34">│</span> <span class="ansi1">Prerelease:</span> No                                                                                 <span class="ansi34">│</span>
<span class="ansi34">│</span> <span class="ansi1">Checksum Verification:</span> Enabled                                                                 <span class="ansi34">│</span>
<span class="ansi34">│</span>   <span class="ansi2">Algorithm:</span> SHA256                                                                            <span class="ansi34">│</span>
<span class="ansi34">│</span>   <span class="ansi2">Pattern:</span> {filename}-SHA256.txt                                                               <span class="ansi34">│</span>
<span class="ansi34">│</span>   <span class="ansi2">Required:</span> No                                                                                 <span class="ansi34">│</span>
<span class="ansi34">│</span> <span class="ansi1">File Rotation:</span> Disabled                                                                        <span class="ansi34">│</span>
<span class="ansi34">╰────────────────────────────────────────────────────────────────────────────────────────────────╯</span>
<span class="ansi32">╭─</span><span class="ansi32">───────────────────────────────────────────</span><span class="ansi32"> Files </span><span class="ansi32">────────────────────────────────────────────</span><span class="ansi32">─╮</span>
<span class="ansi32">│</span> <span class="ansi1">FreeCAD_1.0.2-conda-Linux-x86_64-py311.AppImage</span>                                                <span class="ansi32">│</span>
<span class="ansi32">│</span>   <span class="ansi2">Size:</span> 759.0 MB                                                                               <span class="ansi32">│</span>
<span class="ansi32">│</span>   <span class="ansi2">Modified:</span> 2025-09-14 00:25:50                                                                <span class="ansi32">│</span>
<span class="ansi32">│</span>   <span class="ansi2">Executable:</span> <span class="ansi32">executable</span>                                                                       <span class="ansi32">│</span>
<span class="ansi32">│</span>                                                                                                <span class="ansi32">│</span>
<span class="ansi32">│</span> <span class="ansi1">FreeCAD-1.0.0-conda-Linux-x86_64-py311.appimage</span>                                                <span class="ansi32">│</span>
<span class="ansi32">│</span>   <span class="ansi2">Size:</span> 648.2 MB                                                                               <span class="ansi32">│</span>
<span class="ansi32">│</span>   <span class="ansi2">Modified:</span> 2024-11-30 15:22:39                                                                <span class="ansi32">│</span>
<span class="ansi32">│</span>   <span class="ansi2">Executable:</span> <span class="ansi32">executable</span>                                                                       <span class="ansi32">│</span>
<span class="ansi32">╰────────────────────────────────────────────────────────────────────────────────────────────────╯</span>
<span class="ansi33">╭─</span><span class="ansi33">──────────────────────────────────────────</span><span class="ansi33"> Symlinks </span><span class="ansi33">──────────────────────────────────────────</span><span class="ansi33">─╮</span>
<span class="ansi33">│</span> <span class="ansi33">No symlinks found pointing to AppImage files</span>                                                   <span class="ansi33">│</span>
<span class="ansi33">╰────────────────────────────────────────────────────────────────────────────────────────────────╯</span>

</pre>
</body>

</html>

To see the two new apps that are being managed:

```bash
➤ appimage-updater list
```

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">

<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title></title>
<style type="text/css">
.ansi2html-content { display: inline; white-space: pre-wrap; word-wrap: break-word; }
.body_foreground { color: #AAAAAA; }
.body_background { background-color: #000000; }
.inv_foreground { color: #000000; }
.inv_background { background-color: #AAAAAA; }
.ansi1 { font-weight: bold; }
.ansi3 { font-style: italic; }
.ansi32 { color: #00aa00; }
.ansi33 { color: #aa5500; }
.ansi34 { color: #0000aa; }
.ansi35 { color: #E850A8; }
.ansi36 { color: #00aaaa; }
</style>
</head>
<body class="body_foreground body_background">
<pre class="ansi2html-content" style="font-size: 60%;">
<span class="ansi3">                                                          Configured Applications                                                          </span>
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃<span class="ansi1"> </span><span class="ansi1">Application      </span><span class="ansi1"> </span>┃<span class="ansi1"> </span><span class="ansi1">Status </span><span class="ansi1"> </span>┃<span class="ansi1"> </span><span class="ansi1">Source                                                                </span><span class="ansi1"> </span>┃<span class="ansi1"> </span><span class="ansi1">Download Directory              </span><span class="ansi1"> </span>┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│<span class="ansi36"> </span><span class="ansi36">appimaged        </span><span class="ansi36"> </span>│<span class="ansi32"> </span><span class="ansi32">Enabled</span><span class="ansi32"> </span>│<span class="ansi33"> </span><span class="ansi33">https://github.com/probonopd/go-appimage                              </span><span class="ansi33"> </span>│<span class="ansi35"> </span><span class="ansi35">~/Applications/appimaged        </span><span class="ansi35"> </span>│
│<span class="ansi36"> </span><span class="ansi36">appimagetool     </span><span class="ansi36"> </span>│<span class="ansi32"> </span><span class="ansi32">Enabled</span><span class="ansi32"> </span>│<span class="ansi33"> </span><span class="ansi33">https://github.com/AppImage/appimagetool                              </span><span class="ansi33"> </span>│<span class="ansi35"> </span><span class="ansi35">~/Applications/appimagetool     </span><span class="ansi35"> </span>│
│<span class="ansi36"> </span><span class="ansi36">BambuStudio      </span><span class="ansi36"> </span>│<span class="ansi32"> </span><span class="ansi32">Enabled</span><span class="ansi32"> </span>│<span class="ansi33"> </span><span class="ansi33">https://github.com/bambulab/BambuStudio                               </span><span class="ansi33"> </span>│<span class="ansi35"> </span><span class="ansi35">~/Applications/BambuStudio      </span><span class="ansi35"> </span>│
│<span class="ansi36"> </span><span class="ansi36">EdgeTX_Companion </span><span class="ansi36"> </span>│<span class="ansi32"> </span><span class="ansi32">Enabled</span><span class="ansi32"> </span>│<span class="ansi33"> </span><span class="ansi33">https://github.com/EdgeTX/edgetx                                      </span><span class="ansi33"> </span>│<span class="ansi35"> </span><span class="ansi35">~/Applications/EdgeTX           </span><span class="ansi35"> </span>│
│<span class="ansi36"> </span><span class="ansi36">FreeCAD          </span><span class="ansi36"> </span>│<span class="ansi32"> </span><span class="ansi32">Enabled</span><span class="ansi32"> </span>│<span class="ansi33"> </span><span class="ansi33">https://github.com/FreeCAD/FreeCAD                                    </span><span class="ansi33"> </span>│<span class="ansi35"> </span><span class="ansi35">~/Applications/FreeCAD          </span><span class="ansi35"> </span>│
│<span class="ansi36"> </span><span class="ansi36">FreeCAD_weekly   </span><span class="ansi36"> </span>│<span class="ansi32"> </span><span class="ansi32">Enabled</span><span class="ansi32"> </span>│<span class="ansi33"> </span><span class="ansi33">https://github.com/FreeCAD/FreeCAD                                    </span><span class="ansi33"> </span>│<span class="ansi35"> </span><span class="ansi35">~/Applications/FreeCAD_weekly   </span><span class="ansi35"> </span>│
│<span class="ansi36"> </span><span class="ansi36">GitHubDesktop    </span><span class="ansi36"> </span>│<span class="ansi32"> </span><span class="ansi32">Enabled</span><span class="ansi32"> </span>│<span class="ansi33"> </span><span class="ansi33">https://github.com/shiftkey/desktop                                   </span><span class="ansi33"> </span>│<span class="ansi35"> </span><span class="ansi35">~/Applications/GitHubDesktop    </span><span class="ansi35"> </span>│
│<span class="ansi36"> </span><span class="ansi36">InkScape         </span><span class="ansi36"> </span>│<span class="ansi32"> </span><span class="ansi32">Enabled</span><span class="ansi32"> </span>│<span class="ansi33"> </span><span class="ansi33">https://inkscape.org/release/all/gnulinux/appimage/                   </span><span class="ansi33"> </span>│<span class="ansi35"> </span><span class="ansi35">~/Applications/InkScape         </span><span class="ansi35"> </span>│
│<span class="ansi36"> </span><span class="ansi36">Meshlab          </span><span class="ansi36"> </span>│<span class="ansi32"> </span><span class="ansi32">Enabled</span><span class="ansi32"> </span>│<span class="ansi33"> </span><span class="ansi33">https://github.com/cnr-isti-vclab/meshlab                             </span><span class="ansi33"> </span>│<span class="ansi35"> </span><span class="ansi35">~/Applications/Meshlab          </span><span class="ansi35"> </span>│
│<span class="ansi36"> </span><span class="ansi36">OpenRGB          </span><span class="ansi36"> </span>│<span class="ansi32"> </span><span class="ansi32">Enabled</span><span class="ansi32"> </span>│<span class="ansi33"> </span><span class="ansi33">https://codeberg.org/OpenRGB/OpenRGB                                  </span><span class="ansi33"> </span>│<span class="ansi35"> </span><span class="ansi35">~/Applications/OpenRGB          </span><span class="ansi35"> </span>│
│<span class="ansi36"> </span><span class="ansi36">OpenShot         </span><span class="ansi36"> </span>│<span class="ansi32"> </span><span class="ansi32">Enabled</span><span class="ansi32"> </span>│<span class="ansi33"> </span><span class="ansi33">https://github.com/OpenShot/openshot-qt                               </span><span class="ansi33"> </span>│<span class="ansi35"> </span><span class="ansi35">~/Applications/OpenShot         </span><span class="ansi35"> </span>│
│<span class="ansi36"> </span><span class="ansi36">OrcaSlicer       </span><span class="ansi36"> </span>│<span class="ansi32"> </span><span class="ansi32">Enabled</span><span class="ansi32"> </span>│<span class="ansi33"> </span><span class="ansi33">https://github.com/SoftFever/OrcaSlicer                               </span><span class="ansi33"> </span>│<span class="ansi35"> </span><span class="ansi35">~/Applications/OrcaSlicer       </span><span class="ansi35"> </span>│
│<span class="ansi36"> </span><span class="ansi36">OrcaSlicerNightly</span><span class="ansi36"> </span>│<span class="ansi32"> </span><span class="ansi32">Enabled</span><span class="ansi32"> </span>│<span class="ansi33"> </span><span class="ansi33">https://github.com/SoftFever/OrcaSlicer                               </span><span class="ansi33"> </span>│<span class="ansi35"> </span><span class="ansi35">~/Applications/OrcaSlicerNightly</span><span class="ansi35"> </span>│
│<span class="ansi36"> </span><span class="ansi36">OrcaSlicerRC     </span><span class="ansi36"> </span>│<span class="ansi32"> </span><span class="ansi32">Enabled</span><span class="ansi32"> </span>│<span class="ansi33"> </span><span class="ansi33">https://github.com/SoftFever/OrcaSlicer                               </span><span class="ansi33"> </span>│<span class="ansi35"> </span><span class="ansi35">~/Applications/OrcaSlicerRC     </span><span class="ansi35"> </span>│
│<span class="ansi36"> </span><span class="ansi36">ScribusDev       </span><span class="ansi36"> </span>│<span class="ansi32"> </span><span class="ansi32">Enabled</span><span class="ansi32"> </span>│<span class="ansi33"> </span><span class="ansi33">https://sourceforge.net/projects/scribus/files/scribus-devel/1.7.0    </span><span class="ansi33"> </span>│<span class="ansi35"> </span><span class="ansi35">~/Applications/ScribusDev       </span><span class="ansi35"> </span>│
│<span class="ansi36"> </span><span class="ansi36">UltiMaker-Cura   </span><span class="ansi36"> </span>│<span class="ansi32"> </span><span class="ansi32">Enabled</span><span class="ansi32"> </span>│<span class="ansi33"> </span><span class="ansi33">https://github.com/Ultimaker/Cura                                     </span><span class="ansi33"> </span>│<span class="ansi35"> </span><span class="ansi35">~/Applications/UltiMaker-Cura   </span><span class="ansi35"> </span>│
│<span class="ansi36"> </span><span class="ansi36">YubiKey          </span><span class="ansi36"> </span>│<span class="ansi32"> </span><span class="ansi32">Enabled</span><span class="ansi32"> </span>│<span class="ansi33"> </span><span class="ansi33">https://developers.yubico.com/yubikey-manager-qt/Releases/yubikey-mana</span><span class="ansi33"> </span>│<span class="ansi35"> </span><span class="ansi35">~/Applications/YubiKey          </span><span class="ansi35"> </span>│
│<span class="ansi36">                   </span>│<span class="ansi32">         </span>│<span class="ansi33"> </span><span class="ansi33">ger-qt-latest-linux.AppImage                                          </span><span class="ansi33"> </span>│<span class="ansi35">                                  </span>│
└───────────────────┴─────────┴────────────────────────────────────────────────────────────────────────┴──────────────────────────────────┘
<span class="ansi34">Total: </span><span class="ansi1 ansi34">17</span><span class="ansi34"> applications </span><span class="ansi1 ansi34">(</span><span class="ansi1 ansi34">17</span><span class="ansi34"> enabled, </span><span class="ansi1 ansi34">0</span><span class="ansi34"> disabled</span><span class="ansi1 ansi34">)</span>

</pre>
</body>

</html>

You can manually run `appimage-updater check` or integrate it into crontab or your favorite task scheduler.

```bash
➤ appimage-updater check -y
```

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">

<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title></title>
<style type="text/css">
.ansi2html-content { display: inline; white-space: pre-wrap; word-wrap: break-word; }
.body_foreground { color: #AAAAAA; }
.body_background { background-color: #000000; }
.inv_foreground { color: #000000; }
.inv_background { background-color: #AAAAAA; }
.ansi1 { font-weight: bold; }
.ansi3 { font-style: italic; }
.ansi31 { color: #aa0000; }
.ansi32 { color: #00aa00; }
.ansi33 { color: #aa5500; }
.ansi34 { color: #0000aa; }
.ansi35 { color: #E850A8; }
.ansi36 { color: #00aaaa; }
</style>
</head>
<body class="body_foreground body_background">
<pre class="ansi2html-content" style="font-size: 70%;">
<span class="ansi34">Checking </span><span class="ansi1 ansi34">17</span><span class="ansi34"> applications for updates</span><span class="ansi34">...</span>
Starting concurrent checks: <span class="ansi1">[</span><span class="ansi1 ansi36">0</span>/<span class="ansi1 ansi36">17</span><span class="ansi1">]</span> <span class="ansi1">(</span><span class="ansi1 ansi36">0.0</span>%<span class="ansi1">)</span>
Completed appimagetool: <span class="ansi1">[</span><span class="ansi1 ansi36">1</span>/<span class="ansi1 ansi36">17</span><span class="ansi1">]</span> <span class="ansi1">(</span><span class="ansi1 ansi36">5.9</span>%<span class="ansi1">)</span>
Completed appimaged: <span class="ansi1">[</span><span class="ansi1 ansi36">2</span>/<span class="ansi1 ansi36">17</span><span class="ansi1">]</span> <span class="ansi1">(</span><span class="ansi1 ansi36">11.8</span>%<span class="ansi1">)</span>
Completed FreeCAD_weekly: <span class="ansi1">[</span><span class="ansi1 ansi36">3</span>/<span class="ansi1 ansi36">17</span><span class="ansi1">]</span> <span class="ansi1">(</span><span class="ansi1 ansi36">17.6</span>%<span class="ansi1">)</span>
Completed EdgeTX_Companion: <span class="ansi1">[</span><span class="ansi1 ansi36">4</span>/<span class="ansi1 ansi36">17</span><span class="ansi1">]</span> <span class="ansi1">(</span><span class="ansi1 ansi36">23.5</span>%<span class="ansi1">)</span>
Completed YubiKey: <span class="ansi1">[</span><span class="ansi1 ansi36">5</span>/<span class="ansi1 ansi36">17</span><span class="ansi1">]</span> <span class="ansi1">(</span><span class="ansi1 ansi36">29.4</span>%<span class="ansi1">)</span>
Completed BambuStudio: <span class="ansi1">[</span><span class="ansi1 ansi36">6</span>/<span class="ansi1 ansi36">17</span><span class="ansi1">]</span> <span class="ansi1">(</span><span class="ansi1 ansi36">35.3</span>%<span class="ansi1">)</span>
Completed UltiMaker-Cura: <span class="ansi1">[</span><span class="ansi1 ansi36">7</span>/<span class="ansi1 ansi36">17</span><span class="ansi1">]</span> <span class="ansi1">(</span><span class="ansi1 ansi36">41.2</span>%<span class="ansi1">)</span>
Completed GitHubDesktop: <span class="ansi1">[</span><span class="ansi1 ansi36">8</span>/<span class="ansi1 ansi36">17</span><span class="ansi1">]</span> <span class="ansi1">(</span><span class="ansi1 ansi36">47.1</span>%<span class="ansi1">)</span>
Completed FreeCAD: <span class="ansi1">[</span><span class="ansi1 ansi36">9</span>/<span class="ansi1 ansi36">17</span><span class="ansi1">]</span> <span class="ansi1">(</span><span class="ansi1 ansi36">52.9</span>%<span class="ansi1">)</span>
Completed OrcaSlicer: <span class="ansi1">[</span><span class="ansi1 ansi36">10</span>/<span class="ansi1 ansi36">17</span><span class="ansi1">]</span> <span class="ansi1">(</span><span class="ansi1 ansi36">58.8</span>%<span class="ansi1">)</span>
Completed OrcaSlicerNightly: <span class="ansi1">[</span><span class="ansi1 ansi36">11</span>/<span class="ansi1 ansi36">17</span><span class="ansi1">]</span> <span class="ansi1">(</span><span class="ansi1 ansi36">64.7</span>%<span class="ansi1">)</span>
Completed OrcaSlicerRC: <span class="ansi1">[</span><span class="ansi1 ansi36">12</span>/<span class="ansi1 ansi36">17</span><span class="ansi1">]</span> <span class="ansi1">(</span><span class="ansi1 ansi36">70.6</span>%<span class="ansi1">)</span>
Completed Meshlab: <span class="ansi1">[</span><span class="ansi1 ansi36">13</span>/<span class="ansi1 ansi36">17</span><span class="ansi1">]</span> <span class="ansi1">(</span><span class="ansi1 ansi36">76.5</span>%<span class="ansi1">)</span>
Completed OpenShot: <span class="ansi1">[</span><span class="ansi1 ansi36">14</span>/<span class="ansi1 ansi36">17</span><span class="ansi1">]</span> <span class="ansi1">(</span><span class="ansi1 ansi36">82.4</span>%<span class="ansi1">)</span>
Completed OpenRGB: <span class="ansi1">[</span><span class="ansi1 ansi36">15</span>/<span class="ansi1 ansi36">17</span><span class="ansi1">]</span> <span class="ansi1">(</span><span class="ansi1 ansi36">88.2</span>%<span class="ansi1">)</span>
Completed InkScape: <span class="ansi1">[</span><span class="ansi1 ansi36">16</span>/<span class="ansi1 ansi36">17</span><span class="ansi1">]</span> <span class="ansi1">(</span><span class="ansi1 ansi36">94.1</span>%<span class="ansi1">)</span>
Completed ScribusDev: <span class="ansi1">[</span><span class="ansi1 ansi36">17</span>/<span class="ansi1 ansi36">17</span><span class="ansi1">]</span> <span class="ansi1">(</span><span class="ansi1 ansi36">100.0</span>%<span class="ansi1">)</span>
<span class="ansi3">                                  Update Check Results                                  </span>
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃<span class="ansi1"> </span><span class="ansi1">Application      </span><span class="ansi1"> </span>┃<span class="ansi1"> </span><span class="ansi1">Status    </span><span class="ansi1"> </span>┃<span class="ansi1"> </span><span class="ansi1">Current Version</span><span class="ansi1"> </span>┃<span class="ansi1"> </span><span class="ansi1">Latest Version</span><span class="ansi1"> </span>┃<span class="ansi1"> </span><span class="ansi1">Update Available</span><span class="ansi1"> </span>┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│<span class="ansi36"> </span><span class="ansi36">appimaged        </span><span class="ansi36"> </span>│<span class="ansi35"> </span><span class="ansi32">Up to date</span><span class="ansi35"> </span>│<span class="ansi33"> </span><span class="ansi33">continuous     </span><span class="ansi33"> </span>│<span class="ansi32"> </span><span class="ansi32">continuous    </span><span class="ansi32"> </span>│<span class="ansi31"> </span><span class="ansi31">No              </span><span class="ansi31"> </span>│
│<span class="ansi36"> </span><span class="ansi36">appimagetool     </span><span class="ansi36"> </span>│<span class="ansi35"> </span><span class="ansi32">Up to date</span><span class="ansi35"> </span>│<span class="ansi33"> </span><span class="ansi33">continuous     </span><span class="ansi33"> </span>│<span class="ansi32"> </span><span class="ansi32">continuous    </span><span class="ansi32"> </span>│<span class="ansi31"> </span><span class="ansi31">No              </span><span class="ansi31"> </span>│
│<span class="ansi36"> </span><span class="ansi36">BambuStudio      </span><span class="ansi36"> </span>│<span class="ansi35"> </span><span class="ansi32">Up to date</span><span class="ansi35"> </span>│<span class="ansi33"> </span><span class="ansi33">02.02.02       </span><span class="ansi33"> </span>│<span class="ansi32"> </span><span class="ansi32">02.02.02      </span><span class="ansi32"> </span>│<span class="ansi31"> </span><span class="ansi31">No              </span><span class="ansi31"> </span>│
│<span class="ansi36"> </span><span class="ansi36">EdgeTX_Companion </span><span class="ansi36"> </span>│<span class="ansi35"> </span><span class="ansi32">Up to date</span><span class="ansi35"> </span>│<span class="ansi33"> </span><span class="ansi33">2.11.3         </span><span class="ansi33"> </span>│<span class="ansi32"> </span><span class="ansi32">2.11.3        </span><span class="ansi32"> </span>│<span class="ansi31"> </span><span class="ansi31">No              </span><span class="ansi31"> </span>│
│<span class="ansi36"> </span><span class="ansi36">FreeCAD          </span><span class="ansi36"> </span>│<span class="ansi35"> </span><span class="ansi32">Up to date</span><span class="ansi35"> </span>│<span class="ansi33"> </span><span class="ansi33">1.0.2          </span><span class="ansi33"> </span>│<span class="ansi32"> </span><span class="ansi32">1.0.2         </span><span class="ansi32"> </span>│<span class="ansi31"> </span><span class="ansi31">No              </span><span class="ansi31"> </span>│
│<span class="ansi36"> </span><span class="ansi36">FreeCAD_weekly   </span><span class="ansi36"> </span>│<span class="ansi35"> </span><span class="ansi32">Up to date</span><span class="ansi35"> </span>│<span class="ansi33"> </span><span class="ansi33">2025.10.08     </span><span class="ansi33"> </span>│<span class="ansi32"> </span><span class="ansi32">2025.10.08    </span><span class="ansi32"> </span>│<span class="ansi31"> </span><span class="ansi31">No              </span><span class="ansi31"> </span>│
│<span class="ansi36"> </span><span class="ansi36">GitHubDesktop    </span><span class="ansi36"> </span>│<span class="ansi35"> </span><span class="ansi32">Up to date</span><span class="ansi35"> </span>│<span class="ansi33"> </span><span class="ansi33">3.4.13         </span><span class="ansi33"> </span>│<span class="ansi32"> </span><span class="ansi32">3.4.13        </span><span class="ansi32"> </span>│<span class="ansi31"> </span><span class="ansi31">No              </span><span class="ansi31"> </span>│
│<span class="ansi36"> </span><span class="ansi36">InkScape         </span><span class="ansi36"> </span>│<span class="ansi35"> </span><span class="ansi32">Up to date</span><span class="ansi35"> </span>│<span class="ansi33"> </span><span class="ansi33">1.4.2          </span><span class="ansi33"> </span>│<span class="ansi32"> </span><span class="ansi32">1.4.2         </span><span class="ansi32"> </span>│<span class="ansi31"> </span><span class="ansi31">No              </span><span class="ansi31"> </span>│
│<span class="ansi36"> </span><span class="ansi36">Meshlab          </span><span class="ansi36"> </span>│<span class="ansi35"> </span><span class="ansi32">Up to date</span><span class="ansi35"> </span>│<span class="ansi33"> </span><span class="ansi33">2025.07        </span><span class="ansi33"> </span>│<span class="ansi32"> </span><span class="ansi32">2025.07       </span><span class="ansi32"> </span>│<span class="ansi31"> </span><span class="ansi31">No              </span><span class="ansi31"> </span>│
│<span class="ansi36"> </span><span class="ansi36">OpenRGB          </span><span class="ansi36"> </span>│<span class="ansi35"> </span><span class="ansi32">Up to date</span><span class="ansi35"> </span>│<span class="ansi33"> </span><span class="ansi33">0.9            </span><span class="ansi33"> </span>│<span class="ansi32"> </span><span class="ansi32">0.9           </span><span class="ansi32"> </span>│<span class="ansi31"> </span><span class="ansi31">No              </span><span class="ansi31"> </span>│
│<span class="ansi36"> </span><span class="ansi36">OpenShot         </span><span class="ansi36"> </span>│<span class="ansi35"> </span><span class="ansi32">Up to date</span><span class="ansi35"> </span>│<span class="ansi33"> </span><span class="ansi33">3.3.0          </span><span class="ansi33"> </span>│<span class="ansi32"> </span><span class="ansi32">3.3.0         </span><span class="ansi32"> </span>│<span class="ansi31"> </span><span class="ansi31">No              </span><span class="ansi31"> </span>│
│<span class="ansi36"> </span><span class="ansi36">OrcaSlicer       </span><span class="ansi36"> </span>│<span class="ansi35"> </span><span class="ansi32">Up to date</span><span class="ansi35"> </span>│<span class="ansi33"> </span><span class="ansi33">2.3.1          </span><span class="ansi33"> </span>│<span class="ansi32"> </span><span class="ansi32">2.3.1         </span><span class="ansi32"> </span>│<span class="ansi31"> </span><span class="ansi31">No              </span><span class="ansi31"> </span>│
│<span class="ansi36"> </span><span class="ansi36">OrcaSlicerNightly</span><span class="ansi36"> </span>│<span class="ansi35"> </span><span class="ansi32">Up to date</span><span class="ansi35"> </span>│<span class="ansi33"> </span><span class="ansi33">2025-10-08     </span><span class="ansi33"> </span>│<span class="ansi32"> </span><span class="ansi32">2025-10-13    </span><span class="ansi32"> </span>│<span class="ansi31"> </span><span class="ansi31">Yes             </span><span class="ansi31"> </span>│
│<span class="ansi36"> </span><span class="ansi36">OrcaSlicerRC     </span><span class="ansi36"> </span>│<span class="ansi35"> </span><span class="ansi32">Up to date</span><span class="ansi35"> </span>│<span class="ansi33"> </span><span class="ansi33">2.3.1-beta     </span><span class="ansi33"> </span>│<span class="ansi32"> </span><span class="ansi32">2.3.1-beta    </span><span class="ansi32"> </span>│<span class="ansi31"> </span><span class="ansi31">No              </span><span class="ansi31"> </span>│
│<span class="ansi36"> </span><span class="ansi36">ScribusDev       </span><span class="ansi36"> </span>│<span class="ansi35"> </span><span class="ansi32">Up to date</span><span class="ansi35"> </span>│<span class="ansi33"> </span><span class="ansi33">1.7.0          </span><span class="ansi33"> </span>│<span class="ansi32"> </span><span class="ansi32">1.7.0         </span><span class="ansi32"> </span>│<span class="ansi31"> </span><span class="ansi31">No              </span><span class="ansi31"> </span>│
│<span class="ansi36"> </span><span class="ansi36">UltiMaker-Cura   </span><span class="ansi36"> </span>│<span class="ansi35"> </span><span class="ansi32">Up to date</span><span class="ansi35"> </span>│<span class="ansi33"> </span><span class="ansi33">5.10.2         </span><span class="ansi33"> </span>│<span class="ansi32"> </span><span class="ansi32">5.10.2        </span><span class="ansi32"> </span>│<span class="ansi31"> </span><span class="ansi31">No              </span><span class="ansi31"> </span>│
│<span class="ansi36"> </span><span class="ansi36">YubiKey          </span><span class="ansi36"> </span>│<span class="ansi35"> </span><span class="ansi32">Up to date</span><span class="ansi35"> </span>│<span class="ansi33"> </span><span class="ansi33">2024-04-18     </span><span class="ansi33"> </span>│<span class="ansi32"> </span><span class="ansi32">2024-04-18    </span><span class="ansi32"> </span>│<span class="ansi31"> </span><span class="ansi31">No              </span><span class="ansi31"> </span>│
└───────────────────┴────────────┴─────────────────┴────────────────┴──────────────────┘
<span class="ansi32">1 update available</span>
<span class="ansi32"></span>
<span class="ansi32">Downloading 1 updates...</span>
<span class="ansi32">OrcaSlicerNightly ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 114.4/114.4 MB • 3.7 MB/s • 0:00:00</span>
<span class="ansi32"></span>
<span class="ansi32">Successfully downloaded 1 updates:</span>
<span class="ansi32">  Downloaded: OrcaSlicerNightly (109.1 MB)</span>
</pre>
</body>
</html>

## Usage

**Quick Commands:**

```bash
# Add applications (configuration is created automatically)
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Apps/FreeCAD
appimage-updater add --prerelease --rotation VSCode https://github.com/microsoft/vscode ~/Apps/VSCode

# Check for updates
appimage-updater check                    # All applications
appimage-updater check --dry-run          # Check only, no downloads
appimage-updater check FreeCAD            # Specific application

# Manage applications
appimage-updater list --format json            # List all configured apps as a JSON file
appimage-updater show FreeCAD             # Show app details
appimage-updater edit FreeCAD --prerelease # Enable prereleases
appimage-updater remove OldApp            # Remove application
```

For complete command documentation, see the [Usage Guide](https://royw.github.io/appimage-updater/usage/).

## Features

- **Easy Application Setup**: Simple `add` command with intelligent defaults
- **File Rotation & Symlinks**: Automatic file management with configurable retention (fixed naming)
- **Flexible Configuration**: Custom rotation settings and symlink management
- **Multi-Format Support**: Works with `.zip`, `.AppImage`, and other release formats seamlessly
- **Batch Operations**: Download multiple updates concurrently with retry logic
- **GitHub Integration**: Full support for releases, prereleases, and asset detection
- **Automatic Checksum Verification**: SHA256, SHA1, MD5 support for download security
- **Progress Tracking**: Visual feedback with transfer speeds and ETAs
- **Robust Error Handling**: Automatic retries with exponential backoff
- **Intelligent Architecture Filtering**: Automatically eliminates incompatible downloads based on CPU architecture (x86_64, arm64, etc.) and supported Linux formats
- **Distribution-Aware Selection**: Automatically selects the best compatible distribution (Ubuntu, Fedora, Debian, Arch, etc.)
- **Smart Auto-Detection**: Automatically detects continuous build repositories and enables prerelease support
- **Version Metadata System**: Accurate version tracking with `.info` files (a text file containing the version) for complex release formats
- **Enhanced ZIP Support**: Automatically extracts AppImages from ZIP files with intelligent error handling
- **Smart Pattern Matching**: Handles naming variations (underscore/hyphen) and character substitutions

### Enhanced ZIP Support

Comprehensive support for applications that distribute AppImage files inside ZIP archives:

```bash
# Applications like EdgeTX Companion that provide ZIP files containing AppImages
appimage-updater add EdgeTX_Companion https://github.com/EdgeTX/edgetx-companion ~/Apps/EdgeTX

# Automatic ZIP extraction workflow:
# 1. Downloads: EdgeTX-Companion-2.9.4-x64.zip
# 2. Extracts: EdgeTX-Companion-2.9.4-x64.AppImage (made executable)
# 3. Creates: EdgeTX-Companion-2.9.4-x64.AppImage.info (version metadata)
# 4. Removes: Original ZIP file
```

### Architecture & Distribution Support

#### Intelligent Compatibility Filtering

Automatically eliminates incompatible downloads:

```bash
# Multi-architecture project (e.g., BalenaEtcher)
# Available: linux-x86_64.AppImage, linux-arm64.AppImage, darwin.dmg, win32.exe
uv run python -m appimage_updater add BalenaEtcher https://github.com/balena-io/etcher ~/Apps/BalenaEtcher
# On a Ubuntu x86_64 system, appimage-updater will automatically select Linux x86_64 AppImage
# Filters out: ARM64, macOS, Windows versions (non-Linux platforms ignored)
```

Note that the module name uses an underscore instead of a hyphen (`uv run python -m appimage_updater`).  This is a python quirk.

**System Detection:**

- **Architecture**: x86_64, amd64, arm64, armv7l, i686 (with intelligent aliasing)
- **Platform**: Linux only (AppImage is Linux-specific)
- **Format Support**: .AppImage, .zip (that contains a .AppImage)

**For Distribution-Specific Releases:**

```bash
# Automatically selects best distribution match
uv run python -m appimage_updater add BambuStudio https://github.com/bambulab/BambuStudio ~/Apps/BambuStudio
# Ubuntu 25.04 → Selects ubuntu-24.04 (closest compatible)
# Fedora 38 → Selects fedora version
# Gentoo → Shows interactive selection menu
```

**Supported Distributions:**

- Ubuntu/Debian family (automatic compatibility)
- Fedora/CentOS/RHEL family (automatic compatibility)
- openSUSE/SUSE family (automatic compatibility)
- Arch/Manjaro family (automatic compatibility)
- Other distributions (interactive selection)

## Configuration

Each monitored application has its own configuration file specifying:

- Source URL (e.g., GitHub releases)
- Target download directory
- File pattern matching for AppImage files
- **Checksum verification settings** (optional, recommended for security)

## Supported Repository Types

AppImage Updater supports multiple repository types with comprehensive documentation for each:

- **[GitHub Repositories](docs/github-support.md)** - Full support for GitHub releases API with authentication and enterprise support
- **[GitLab Repositories](docs/gitlab-support.md)** - Complete GitLab integration for both gitlab.com and self-hosted instances
- **[SourceForge Repositories](docs/sourceforge-support.md)** - Complete SourceForge integration for both sourceforge.net and self-hosted instances
- **[Direct Download URLs](docs/direct-support.md)** - Static download links, "latest" symlinks, and dynamic download pages

Each repository type has detailed documentation covering setup, authentication, troubleshooting, and advanced features.

## Unsupported Applications

Some applications cannot be automatically monitored due to technical limitations:

### LM Studio

- **Issue**: Uses complex JavaScript-generated download URLs with dynamic dropdown selectors
- **Workaround**: Download manually from [lmstudio.ai/download](https://lmstudio.ai/download) and place in your configured directory
- **Alternative**: Monitor their [beta releases page](https://lmstudio.ai/beta-releases) for direct download links

### Applications with OAuth/Login Requirements

Applications requiring authentication or login cannot be automatically monitored.

### Applications with CAPTCHA Protection

Download pages with CAPTCHA verification are not supported for automated access.

## Project Status

**Continuous Integration** - Full CI pipeline with automated testing and documentation\
**Live Documentation** - Documentation site with enhanced navigation using github pages\
**Open Source** - Public repository with contribution guidelines and templates\
**Tools** - Built with Python 3.13 (local) and 3.11 & 3.12 (ci), uv, ruff, mypy, pytest

## Documentation

### **[Complete Documentation → https://royw.github.io/appimage-updater/](https://royw.github.io/appimage-updater/)**

Our comprehensive documentation is live and automatically updated:

**User Guides:**

- **[Getting Started](https://royw.github.io/appimage-updater/getting-started/)** - Step-by-step tutorial and basic usage
- **[Installation](https://royw.github.io/appimage-updater/installation/)** - Complete installation methods and troubleshooting
- **[Usage Guide](https://royw.github.io/appimage-updater/usage/)** - Complete CLI command reference
- **[Configuration](https://royw.github.io/appimage-updater/configuration/)** - Advanced configuration options
- **[Examples](https://royw.github.io/appimage-updater/examples/)** - Practical usage patterns and workflows

**Feature Guides:**

- **[ZIP Support](https://royw.github.io/appimage-updater/zip-support/)** - Handling applications distributed in ZIP files
- **[Rotation Guide](https://royw.github.io/appimage-updater/rotation/)** - File rotation and symlink management
- **[Compatibility System](https://royw.github.io/appimage-updater/compatibility/)** - Distribution compatibility and selection

**Support & Maintenance:**

- **[Security Guide](https://royw.github.io/appimage-updater/security/)** - Authentication, checksums, and security best practices
- **[Troubleshooting](https://royw.github.io/appimage-updater/troubleshooting/)** - Common issues, solutions, and diagnostics
- **[Changelog](https://royw.github.io/appimage-updater/changelog/)** - Version history and release notes

**Developer Resources:**

- **[Architecture](https://royw.github.io/appimage-updater/architecture/)** - System design and component overview
- **[Developer Commands](https://royw.github.io/appimage-updater/commands/)** - Task automation and development tools
- **[Development](https://royw.github.io/appimage-updater/development/)** - Setting up development environment
- **[Testing Guide](https://royw.github.io/appimage-updater/testing/)** - Running tests and quality checks
- **[Contributing](https://royw.github.io/appimage-updater/contributing/)** - Guidelines for contributing to the project

## Development

### Prerequisites

- Python 3.11 or higher
- pipx (for recommended installation) or pip
- git
- pymarkdownlint
- uv package manager
- Task runner (taskfile.dev)

**Quick Start:**

```bash
# Clone and setup
git clone https://github.com/royw/appimage-updater.git
cd appimage-updater
uv sync --extra dev

# Run tests
task test

# Code quality
task check

# Build package
task make
```

For complete development setup, testing procedures, and contribution guidelines, see:

- [Development Guide](https://royw.github.io/appimage-updater/development/)
- [Developer Commands](https://royw.github.io/appimage-updater/commands/)
- [Contributing Guide](https://royw.github.io/appimage-updater/contributing/)

## License

MIT License
