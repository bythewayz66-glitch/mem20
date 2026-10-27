package Mem20::Error;
use strict;
use warnings;
use overload '""' => sub { $_[0]->{message} }, fallback => 1;

# Base class for every error the SDK raises.
#
# Deliberately hand-rolled rather than built on Exception::Class: the whole
# point of this SDK is that it installs with no non-core dependencies, so the
# exception hierarchy is a handful of tiny packages instead of one CPAN
# prerequisite.

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

# A locally rejected argument. Derives from ConfigurationError so existing
# `isa('Mem20::ConfigurationError')` handlers keep working after this class was
# introduced; `isa('Mem20::ValidationError')` is available when the distinction
# matters.
package Mem20::ValidationError;
use strict;
use warnings;
our @ISA = ('Mem20::ConfigurationError');

sub new {
    my ($class, %args) = @_;
    my $self = $class->SUPER::new(%args);
    $self->{tool}   = $args{tool};
    $self->{params} = $args{params};
    return $self;
}

sub tool   { $_[0]{tool} }
sub params { $_[0]{params} }

package Mem20::TransportError;
use strict;
use warnings;
our @ISA = ('Mem20::Error');

# A tool-level failure reported by the server.
#
# Two distinct protocol shapes collapse into this one class, because callers
# care that the tool failed, not which of the server's two failure idioms it
# used (see sdk/perl/AUDIT.md for the transcripts):
#
#   is_error   => 1   the envelope carried result.isError = true
#   soft_error => 1   the envelope said isError = false but the text payload
#                     begins with "Error" (mem20's tool-internal failure path)
package Mem20::ToolError;
use strict;
use warnings;
our @ISA = ('Mem20::Error');

sub new {
    my ($class, %args) = @_;
    my $self = $class->SUPER::new(%args);
    $self->{code}       = $args{code};
    $self->{data}       = $args{data};
    $self->{tool}       = $args{tool};
    $self->{is_error}   = $args{is_error}   ? 1 : 0;
    $self->{soft_error} = $args{soft_error} ? 1 : 0;
    return $self;
}

sub code       { $_[0]{code} }
sub data       { $_[0]{data} }
sub tool       { $_[0]{tool} }
sub is_error   { $_[0]{is_error} }
sub soft_error { $_[0]{soft_error} }

# A background job that never reached a terminal state.
#
# This is raised rather than returned because the alternative is a value that
# looks like success: mem20 answers `{"status":"running","result":null}` while
# the job is still going, and handing that back from wait_for_job means a
# caller who checks `if ($final)` or reads ->{result} sees a completed-looking
# answer with no data in it. The job may still be running on the server, so
# this is not the same failure as a crash -- but it is not an answer either.
package Mem20::JobTimeoutError;
use strict;
use warnings;
our @ISA = ('Mem20::Error');

sub new {
    my ($class, %args) = @_;
    my $self = $class->SUPER::new(%args);
    $self->{job_id}   = $args{job_id};
    $self->{status}   = $args{status};
    $self->{polls}    = $args{polls};
    $self->{timeout}  = $args{timeout};
    $self->{last}     = $args{last};
    return $self;
}

sub job_id  { $_[0]{job_id} }
sub status  { $_[0]{status} }
sub polls   { $_[0]{polls} }
sub timeout { $_[0]{timeout} }

# The last status hashref observed. Useful for logging, but do NOT treat it as
# a result: the job had not finished, which is why this exception exists.
sub last { $_[0]{last} }

# A background job that finished in a state carrying no result.
#
# mem20's three non-running terminal states are `ok` (carries the result),
# `error` (carries an error string, result null) and `not_found` (the server
# never issued that job_id). The last two are failures; reporting them as a
# returned status would make a lost job indistinguishable from an empty answer.
package Mem20::JobFailedError;
use strict;
use warnings;
our @ISA = ('Mem20::Error');

sub new {
    my ($class, %args) = @_;
    my $self = $class->SUPER::new(%args);
    $self->{job_id} = $args{job_id};
    $self->{status} = $args{status};
    $self->{last}   = $args{last};
    return $self;
}

sub job_id { $_[0]{job_id} }
sub status { $_[0]{status} }
sub last   { $_[0]{last} }

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

    eval { $client->memory_store(content => 'x', epistemic_status => 'observed') };
    if (my $err = $@) {
        if (ref $err && $err->isa('Mem20::ToolError')) {
            warn "server said: " . $err->message . "\n";
            warn "tool: "       . ($err->tool // '?') . "\n";
            warn "soft error\n" if $err->soft_error;
        }
    }

=head1 CLASSES

=over 4

=item B<Mem20::Error> - base class; stringifies to its message.

=item B<Mem20::ConfigurationError> - bad options, out-of-range values, unknown keys.

=item B<Mem20::ValidationError> - a tool argument rejected I<locally> before it
was sent, because it violates the tool's own advertised C<inputSchema>.
Derives from C<Mem20::ConfigurationError>. Carries C<tool> and C<params>.

=item B<Mem20::TransportError> - the child server could not be started, died,
timed out, or emitted non-JSON.

=item B<Mem20::ToolError> - the call reached the server and failed there.
Carries C<code>/C<data> for a JSON-RPC error object, and C<tool>, C<is_error>,
C<soft_error> for a tool-level failure inside a successful response.

=item B<Mem20::JobTimeoutError> - a background job did not reach a terminal
state before the deadline. Carries C<job_id>, C<status> (the last status seen),
C<polls>, C<timeout> and C<last>. The job may still be running server-side; what
did not happen is an answer.

=item B<Mem20::JobFailedError> - a background job reached a terminal state that
carries no result: C<status> C<error> (with the server's own error text in the
message) or C<not_found> (the server never issued that C<job_id>). Carries
C<job_id>, C<status> and C<last>.

=back

=head1 JOB FAILURES

A long-running tool answers with a job envelope rather than a result, so its
failure is one poll removed from the C<tools/call> response and none of the
three shapes above can carry it. C<wait_for_job> therefore raises
C<Mem20::JobTimeoutError> instead of returning a still-C<running> status, and
C<Mem20::JobFailedError> for a terminal C<error>/C<not_found>. Both derive from
C<Mem20::Error>, so one C<eval> catches everything.

=head1 TWO FAILURE SHAPES

mem20 does not report every tool failure as a JSON-RPC error object. A JSON-RPC
error object (unknown I<method>) throws a C<ToolError> from the transport. But
an unknown I<tool>, and a handler exception, come back as a B<successful>
JSON-RPC response whose envelope sets C<result.isError>; and a tool-internal
failure (for example a rejected C<epistemic_status>) comes back with
C<result.isError> B<false> and a text payload starting with C<Error>. The client
raises C<ToolError> for all three and flags the third as C<soft_error>.

=cut
