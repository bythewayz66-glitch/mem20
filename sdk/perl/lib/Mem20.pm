package Mem20;
use strict;
use warnings;

use Mem20::Version ();
use Mem20::Errors;
use Mem20::Config;
use Mem20::Transport::Stdio;
use Mem20::Client;

# mem20 Perl SDK.
#
# A persistent memory + cognition substrate for AI agents. This module is an
# idiomatic Perl client for the mem20 MCP server (JSON-RPC 2.0 over stdio, MCP
# protocol revision 2025-06-18).
#
#   use Mem20;
#
#   Mem20::configure(sub { $_[0]->cwd('/opt/mem20') });
#   Mem20::client->memory_store(content => 'hello', category => 'general');
#
# Everything is optional: Mem20::Client->new works with no configuration at
# all, falling back to defaults plus the MEM20_* environment.

my $CONFIGURATION;
my $CLIENT;

# The active configuration (defaults, then any environment, then overrides).
sub configuration {
    return $CONFIGURATION ||= Mem20::Config->from_env;
}

# Configure the SDK. Called with a block for the Rails-style DSL, or with a
# flat option hash:
#
#   Mem20::configure(sub { $_[0]->cwd('/opt/mem20') });
#   Mem20::configure(health_port => 9090);
#
# The block mutates the config being built; the result is frozen. Any
# previously memoised client is dropped, because it was holding the old one.
sub configure {
    my ($block, %options) = @_;

    if (ref $block eq 'CODE') {
        $CONFIGURATION = Mem20::Config->build($block, %options);
    }
    else {
        %options = ( ( ref $block eq 'HASH' ? %$block : () ), %options );
        $CONFIGURATION = Mem20::Config->build(undef, %options);
    }

    $CLIENT = undef;
    return $CONFIGURATION;
}

sub reset_configuration {
    $CONFIGURATION = undef;
    $CLIENT        = undef;
    return;
}

# A memoised client over the current configuration.
sub client {
    $CLIENT ||= Mem20::Client->new( config => configuration() );
    return $CLIENT;
}

sub reset_client {
    $CLIENT->close if $CLIENT;
    $CLIENT = undef;
    return;
}

1;
__END__

=head1 NAME

Mem20 - Perl SDK for the mem20 memory + cognition server

=head1 SYNOPSIS

    use Mem20;

    Mem20::configure(sub {
        my $c = shift;
        $c->cwd('/opt/mem20');
    });

    my $client = Mem20::client;
    $client->memory_store(content => 'prod runs build 4127', tags => [ 'prod' ]);
    my $hits = $client->memory_recall(query => 'what build is prod on', limit => 5);

    print Mem20::Client::text($hits), "\n";
    print "healthy\n" if $client->healthy;

=head1 DESCRIPTION

A thin, dependency-free client for the mem20 MCP server. It speaks JSON-RPC
2.0 over stdio to a child server process and exposes:

=over 4

=item * the memory primitives (C<memory_store>, C<memory_recall>),

=item * the full tool surface (C<tool>, C<tools>, C<tool_names>), and

=item * dynamic dispatch, so any registered tool is callable by name.

=back

It installs with nothing but core Perl (5.20+): JSON::PP, IPC::Open3,
IO::Select, HTTP::Tiny and Time::HiRes all ship with the interpreter.

=head1 FUNCTIONS

=over 4

=item C<Mem20::configuration()> - the active config object.

=item C<< Mem20::configure($block_or_hash, %options) >> - replace it and drop the client.

=item C<Mem20::client()> - a memoised C<Mem20::Client>.

=item C<Mem20::reset_configuration()>, C<Mem20::reset_client()> - forget memoised state.

=back

=head1 SEE ALSO

L<Mem20::Client>, L<Mem20::Config>, L<Mem20::Errors>,
L<Mem20::Transport::Stdio>. The Ruby gem C<mem20-sdk-ruby> exposes the same
surface with the same names.

=cut
