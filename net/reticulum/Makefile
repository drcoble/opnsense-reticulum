PLUGIN_NAME=		reticulum
PLUGIN_VERSION=		1.1
PLUGIN_REVISION=	0
PLUGIN_COMMENT=		Reticulum Network Stack - Transport & Propagation Node
PLUGIN_MAINTAINER=	maintainer@example.org
PLUGIN_WWW=		https://reticulum.network/
PLUGIN_CATEGORIES=	net
PLUGIN_TIER=		2

# Reticulum and LXMF are installed from bundled source (see src/usr/local/lib/rns-src
# and src/usr/local/lib/lxmf-src git submodules) via pip in +POST_INSTALL.
# Only their compiled/system-level dependencies are listed here as pkg deps.
PLUGIN_DEPENDS=		py311-cryptography py311-serial

# Bundled upstream source versions (update submodules + bump PLUGIN_VERSION to release)
RNS_VERSION=		1.1.3
LXMF_VERSION=		0.9.4

.include "../../Mk/plugins.mk"
