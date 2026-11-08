package Mem20::Version;

use strict;
use warnings;

our $VERSION = '0.2.0';

# The mem20 server release this SDK was built and tested against.
#
# This is NOT the SDK version. The SDK and the server version independently:
# a 0.2.0 SDK talking to a 3.1.2 server is the supported arrangement.
#
# Prefer reporting the value the server actually sent in its initialize reply
# (`Mem20::Client->server_info`) when you need to know what you are really
# talking to; this constant is the baseline the SDK was verified against.
our $SERVER_VERSION = '3.1.2';

# The tool surface this SDK is compiled against.
#
# These are NOT prefix buckets. SURFACE_DOMAIN_COUNT is the number of distinct
# owning domain modules the server registers (39). The figure is read from
# docs/surface.json, which scripts/surface_manifest.py generates from a live
# `tools/list` response and cross-checks against the AST catalog in
# web/src/data/tools.json -- the two collections must be identical or the
# generator refuses to emit. The domain table is in docs/TOOL-DOMAINS.md.
#
# Bucketing the 311 tool NAMES by their first `_` component yields more buckets
# than there are domains, which is why the domain figure must come from
# registration and never from string-splitting tool names.
#
# Verified by a live tools/list round trip; see sdk/perl/AUDIT.md.
our $SURFACE_TOOL_COUNT   = 311;
our $SURFACE_DOMAIN_COUNT = 39;

1;

__END__

=head1 NAME

Mem20::Version - version constants for the mem20 Perl SDK

=head1 DESCRIPTION

Three constants, each answering a different question:

=over 4

=item C<$Mem20::Version::VERSION> - the SDK's own release (0.2.0).

=item C<$Mem20::Version::SERVER_VERSION> - the mem20 server release the SDK
was tested against. A 0.2.0 SDK talking to a 3.1.2 server is expected; they
version independently.

=item C<$Mem20::Version::SURFACE_TOOL_COUNT> - tools the SDK is compiled
against (311), used by C<< Mem20::Client->verify_surface >>.

=item C<$Mem20::Version::SURFACE_DOMAIN_COUNT> - domain modules the server
registers (39). This is a registration count, B<not> a count of tool-name
prefixes; those are two different numbers.

=back

=head1 SEE ALSO

L<Mem20::Client>, L<Mem20::Transport>

=cut
