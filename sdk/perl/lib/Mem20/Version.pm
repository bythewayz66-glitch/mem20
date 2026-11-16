package Mem20::Version;
use strict;
use warnings;

use Mem20::Surface ();

# The SDK version. Tracked independently of the mem20 server release, exactly
# as the Ruby gem does (Mem20::VERSION vs Mem20::SERVER_VERSION).
our $VERSION = '0.3.0';

# The mem20 server release this SDK was validated against.
our $SERVER_VERSION = '4.0.0';

# The MCP protocol revision sent in the `initialize` handshake.
our $PROTOCOL_VERSION = '2025-06-18';

# The tool surface this SDK is compiled against.
#
# These are NOT prefix buckets. SURFACE_DOMAIN_COUNT is the number of distinct
# owning domain modules the server registers (129). The figure is read from
# docs/surface.json, which scripts/surface_manifest.py generates from a live
# `tools/list` response and cross-checks against the AST catalog in
# web/src/data/tools.json -- the two collections must be identical or the
# generator refuses to emit. The domain table is in docs/TOOL-DOMAINS.md.
#
# Bucketing tool NAMES by their first `_` component yields more buckets than
# there are domains, which is why the domain figure must come from
# registration and never from string-splitting tool names.
#
# The numbers are NOT literals here: they are re-exported from Mem20::Surface,
# which xt/gen-surface.pl generates from the repository manifest. That keeps a
# single source of truth and means a surface bump is one regeneration, not a
# hunt for every place a count was typed by hand.
our $SURFACE_TOOL_COUNT   = $Mem20::Surface::TOOL_COUNT;
our $SURFACE_DOMAIN_COUNT = $Mem20::Surface::DOMAIN_COUNT;

1;
__END__

=head1 NAME

Mem20::Version - version constants for the mem20 Perl SDK

=head1 DESCRIPTION

Constants, kept separate on purpose:

=over 4

=item C<$Mem20::Version::VERSION> - this SDK's own version.

=item C<$Mem20::Version::SERVER_VERSION> - the mem20 server release the SDK
was tested against. A 0.3.0 SDK talking to a 4.0.0 server is expected; they
version independently.

=item C<$Mem20::Version::PROTOCOL_VERSION> - the MCP protocol revision used
in the C<initialize> handshake.

=item C<$Mem20::Version::SURFACE_TOOL_COUNT> - tools the SDK is compiled
against (487), used by C<< Mem20::Client->verify_surface >>. Re-exported from
C<$Mem20::Surface::TOOL_COUNT>.

=item C<$Mem20::Version::SURFACE_DOMAIN_COUNT> - domain modules the server
registers (129). This is a registration count, B<not> a count of tool-name
prefixes; those are two different numbers. Re-exported from
C<$Mem20::Surface::DOMAIN_COUNT>.

=back

=head1 SURFACE PROVENANCE

The counts are not typed here. C<xt/gen-surface.pl> reads
C<docs/surface.json> and C<web/src/data/tools.json> from the mem20 repository,
refuses to emit unless the two agree, and writes C<lib/Mem20/Surface.pm> with
the full tool-name list and the tool-to-domain map. This module re-exports the
two counts from it.

That means the SDK can name the exact tools that moved, not just report that a
number changed -- see C<< Mem20::Surface->diff >> and
C<< Mem20::Client->verify_surface >>.

=cut
