package Mem20::Error;
use strict;
use warnings;
use overload '""' => sub { $_[0]->{message} }, fallback => 1;

# Base class for every error the SDK raises.
#
# Deliberately hand-rolled rather than built on Exception::Class: the whole
# point of this SDK is that it installs with no non-core dependencies, so the
# exception hierarchy is four tiny packages instead of one CPAN prerequisite.

sub new {
    my ($class, %args) = @_;
    my $self = bless {
        message => defined $args{message} ? $args{message} : 'mem20 error',
    }, $class;
    return $self;
}

# Throw in the idiomatic Perl way: die with an object that stringifies to the
# message but still carries the class (so `eval { }; $@->isa(...)` works).
sub throw {
    my $class = shift;
    my $self  = $class->new(@_);
    die $self;
}

sub message { $_[0]{message} }

# Run a block and return the exception it threw, or undef if it did not throw.
#
# This exists because the obvious `my $e = eval { ...; $@ }` does NOT work:
# leaving an eval block clears $@, so the expression evaluates to undef even
# when the block died. Capturing $@ in the same statement that ends the eval
# always loses the error.
#
#   my $e = Mem20::Errors::caught(sub { $cfg->health_port(0) });
sub caught {
    my ($code) = @_;
    my $ok = eval { $code->(); 1 };
    return $ok ? undef : $@;
}

# Re-throw a caught error unchanged if it is already ours, otherwise wrap it.
sub rethrow {
    my ($class, $err) = @_;
    die $err if ref $err && $err->isa('Mem20::Error');
    $class->throw(message => "$err");
}

package Mem20::ConfigurationError;
use strict;
use warnings;
our @ISA = ('Mem20::Error');

package Mem20::TransportError;
use strict;
use warnings;
our @ISA = ('Mem20::Error');

package Mem20::ToolError;
use strict;
use warnings;
our @ISA = ('Mem20::Error');

# A tool-level failure reported by the server as a JSON-RPC error object.
# Carries the numeric code and any structured data alongside the message.
sub new {
    my ($class, %args) = @_;
    my $self = $class->SUPER::new(%args);
    $self->{code} = $args{code};
    $self->{data} = $args{data};
    return $self;
}

sub code { $_[0]{code} }
sub data { $_[0]{data} }

# `Mem20::Errors` is the name callers naturally reach for (the file is
# Errors.pm), and it is a friendlier home for the one behaviour that is not a
# method: catching. Both spellings resolve to the same subs.
package Mem20::Errors;
use strict;
use warnings;

sub caught  { Mem20::Error::caught(@_) }
sub rethrow { shift; Mem20::Error::rethrow(@_) }

1;
__END__

=head1 NAME

Mem20::Error - exception hierarchy for the mem20 Perl SDK

=head1 SYNOPSIS

    use Mem20::Errors;

    eval { $client->memory_store(content => 'x') };
    if (my $err = $@) {
        if (ref $err && $err->isa('Mem20::ToolError')) {
            warn "server said: " . $err->message . " (code " . ($err->code // '?') . ")\n";
        }
    }

=head1 CLASSES

=over 4

=item B<Mem20::Error> - base class; stringifies to its message.

=item B<Mem20::ConfigurationError> - bad options, out-of-range values, unknown keys.

=item B<Mem20::TransportError> - the child server could not be started, died, or timed out.

=item B<Mem20::ToolError> - the server answered with a JSON-RPC error object.
Also carries C<code> and C<data>.

=back

=head1 METHODS

=over 4

=item C<< Class->throw(message => ...) >> - construct and C<die> with the object.

=item C<< Class->rethrow($err) >> - pass a Mem20::Error through untouched, wrap anything else.

=item C<message>, C<code>, C<data> - accessors (C<code>/C<data> on ToolError only).

=back

=cut
