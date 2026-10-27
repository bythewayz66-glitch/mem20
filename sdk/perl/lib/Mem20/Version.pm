package Mem20::Version;
use strict;
use warnings;

# The SDK version. Tracked independently of the mem20 server release, exactly
# as the Ruby gem does (Mem20::VERSION vs Mem20::SERVER_VERSION).
our $VERSION = '0.2.0';

# The mem20 server release this SDK was validated against.
our $SERVER_VERSION = '3.0.0';

# The MCP protocol revision sent in the `initialize` handshake.
our $PROTOCOL_VERSION = '2025-06-18';

# The tool surface this SDK is compiled against.
#
# These are NOT prefix buckets. SURFACE_DOMAIN_COUNT is the number of
# `register_*_tools()` domain modules Mem20MCPServer._setup_tools() actually
# invokes (27: memory, cognitive, roadmap, world, procedural, blender, unity,
# integration, a2a, thought_process, cloudservice, cloudstorage, communication,
# database, design, dev, enhanced_memory, filesystem, finance, marketing,
# productivity, search, versioncontrol, webscraping, braid, irc, lie).
#
# The extra inline register_job_tools() group adds job_status and job_wait but
# lives in server.py rather than in mcp/tools/, so it is not a domain module.
# Bucketing the 270 tool NAMES by their first `_` component yields 37 buckets,
# which is why the domain figure must come from registration and never from
# string-splitting tool names.
#
# Verified by instantiating Mem20MCPServer and by a live tools/list round trip;
# see sdk/perl/AUDIT.md for the raw transcripts.
our $SURFACE_TOOL_COUNT   = 270;
our $SURFACE_DOMAIN_COUNT = 27;

1;
__END__

=head1 NAME

Mem20::Version - version constants for the mem20 Perl SDK

=head1 DESCRIPTION

Constants, kept separate on purpose:

=over 4

=item C<$Mem20::Version::VERSION> - this SDK's own version.

=item C<$Mem20::Version::SERVER_VERSION> - the mem20 server release the SDK
was tested against. A 0.2.0 SDK talking to a 3.0.0 server is expected; they
version independently.

=item C<$Mem20::Version::PROTOCOL_VERSION> - the MCP protocol revision used
in the C<initialize> handshake.

=item C<$Mem20::Version::SURFACE_TOOL_COUNT> - tools the SDK is compiled
against (270), used by C<< Mem20::Client->verify_surface >>.

=item C<$Mem20::Version::SURFACE_DOMAIN_COUNT> - domain modules the server
registers (27). This is a registration count, B<not> a count of tool-name
prefixes; those are two different numbers (270 names bucket into 37 prefixes).

=back

=cut
