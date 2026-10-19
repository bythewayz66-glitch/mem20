package Mem20::Version;
use strict;
use warnings;

# The SDK version. Tracked independently of the mem20 server release, exactly
# as the Ruby gem does (Mem20::VERSION vs Mem20::SERVER_VERSION).
our $VERSION = '0.1.0';

# The mem20 server release this SDK was validated against.
our $SERVER_VERSION = '3.0.0';

# The MCP protocol revision sent in the `initialize` handshake.
our $PROTOCOL_VERSION = '2025-06-18';

1;
__END__

=head1 NAME

Mem20::Version - version constants for the mem20 Perl SDK

=head1 DESCRIPTION

Three constants, kept separate on purpose:

=over 4

=item C<$Mem20::Version::VERSION> - this SDK's own version.

=item C<$Mem20::Version::SERVER_VERSION> - the mem20 server release the SDK
was tested against. A 0.1.0 SDK talking to a 3.0.0 server is expected; they
version independently.

=item C<$Mem20::Version::PROTOCOL_VERSION> - the MCP protocol revision used
in the C<initialize> handshake.

=back

=cut
