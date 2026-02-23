PLUGIN_NAME=		reticulum
PLUGIN_VERSION=		1.1
PLUGIN_REVISION=	0
PLUGIN_COMMENT=		Reticulum Network Stack - Transport & Propagation Node
PLUGIN_MAINTAINER=	maintainer@example.org
PLUGIN_WWW=		https://reticulum.network/
PLUGIN_CATEGORIES=	net
PLUGIN_TIER=		2

# Reticulum (RNS) is installed from bundled source (see src/usr/local/lib/rns-src
# git submodule) via pip in +POST_INSTALL.
# Only compiled/system-level dependencies are listed here as pkg deps.
PLUGIN_DEPENDS=		py311-cryptography py311-serial

# Bundled upstream source version (update submodule + bump PLUGIN_VERSION to release)
RNS_VERSION=		1.1.3

.include "../../Mk/plugins.mk"
