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

# The tools mem20 answers with a background-job envelope instead of a result.
#
# Copied verbatim from Mem20MCPServer.LONG_RUNNING_TOOLS in mcp/server.py, not
# inferred from a name prefix: the set is a hand-maintained literal there, and
# it is not derivable from the names (cog_working_memory is a cog_* tool that
# answers inline; beam_search and least_to_most carry no prefix at all).
#
# A caller that does not know this set has to guess whether a response is an
# answer or a job token. Knowing it lets the SDK say so up front, and lets
# t/95-jobs.t drive every member of the set rather than one representative.
#
# Drift is checked, not assumed: t/95-jobs.t re-reads LONG_RUNNING_TOOLS out of
# mcp/server.py when MEM20_MCP_DIR is set and fails if the two disagree.
our @LONG_RUNNING_TOOLS = qw(
    imagination_concept imagination_dream imagination_critique
    imagination_simulate imagination_counterfactual imagination_recombine
    imagination_model imagination_visualize
    cog_process cog_chain cog_reason cog_plan cog_reflect
    tot_reason tot_diagnose tot_modeling
    beam_search least_to_most react_reason
    theory_of_mind_simulate theory_of_mind_perspective
    self_model_reflect memory_auto_consolidate
    cognitive_substrate
);

our %LONG_RUNNING_TOOL = map { $_ => 1 } @LONG_RUNNING_TOOLS;

our $LONG_RUNNING_TOOL_COUNT = scalar @LONG_RUNNING_TOOLS;

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

=item C<@Mem20::Version::LONG_RUNNING_TOOLS> - the 24 tools mem20 answers with
a background-job envelope instead of a result. A compiled copy of
C<Mem20MCPServer.LONG_RUNNING_TOOLS> from F<mcp/server.py>. C<%LONG_RUNNING_TOOL>
is the same set as a lookup hash. F<t/95-jobs.t> compares this list against the
server literal when C<MEM20_MCP_DIR> is set, so a server that gains a
long-running tool fails the suite rather than silently being polled as inline.

=back

=cut
