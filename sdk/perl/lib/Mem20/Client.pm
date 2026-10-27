package Mem20::Client;
use strict;
use warnings;

use Scalar::Util qw(blessed);
use JSON::PP ();
use HTTP::Tiny ();
use Time::HiRes ();

use Mem20::Config;
use Mem20::Errors;
use Mem20::Transport::Stdio;
use Mem20::Version ();

# Threadless, but reentrant-safe: one client owns one transport, and the
# transport serialises calls, so a client can be shared across a whole program
# and handed between modules without coordinating.
#
# The surface mirrors the Ruby gem's Mem20::Client method for method:
#
#   tool / call_tool, tools, tool_names, tool_schemas
#   memory_store, memory_recall
#   health, ready, healthy, metrics
#   close / shutdown
#   dynamic dispatch: any tool the server registers can be called by name
#
# plus ->connect, because Perl has no lazy-attribute idiom as pleasant as
# Ruby's and an explicit handshake is easier to reason about than an implicit
# one. Calls still connect on demand, so connect() is an optimisation, not a
# requirement.

# The knowledge kinds the GROUNDED memory_store tool accepts. Deliberately
# excludes 'imagined': the server's own tool description says invented content
# belongs in the simulated partition (memory_simulate_store), yet the wire
# schema still advertises it and _memory_store() writes it into grounded
# memory. Rejecting it here is the whole point of the partition, so the SDK
# refuses it rather than forwarding it. See sdk/perl/AUDIT.md, section 4.
my @GROUNDED_EPISTEMIC = qw(observed inferred user_stated hypothesis agent_generated unlabeled);
my %GROUNDED_EPISTEMIC = map { $_ => 1 } @GROUNDED_EPISTEMIC;

my @MEMORY_CATEGORIES = qw(user_pref project tool general);
my %MEMORY_CATEGORY   = map { $_ => 1 } @MEMORY_CATEGORIES;

sub new {
    my ($class, %args) = @_;

    my $config = $args{config};
    if (!$config) {
        my %options = map { $_ => $args{$_} } grep { $_ ne 'config' } sort keys %args;
        $config = Mem20::Config->from_env(%options);
    }

    # Freeze: a running client's config must not change underneath it.
    $config->restrict if $config->can('restrict') && !$config->is_frozen;

    my $self = bless {
        config      => $config,
        transport   => undef,
        tool_names  => undef,
        tool_schemas => undef,
        strict      => $args{strict} ? 1 : 0,
        http        => HTTP::Tiny->new( timeout => int( $config->timeout || 30 ) ),
    }, $class;

    return $self;
}

sub config { $_[0]{config} }

# Start the child server and complete the MCP handshake. Idempotent.
sub connect {
    my ($self) = @_;
    $self->_transport->initialize_session;
    return $self;
}

sub _transport {
    my ($self) = @_;
    return $self->{transport} ||= Mem20::Transport::Stdio->new( config => $self->{config} );
}

sub transport { $_[0]->_transport }

# ------------------------------------------------------------------ tool calls

# Call any mem20 tool by name.
#
# Arguments may be a flat pair list (the idiomatic Perl form) or a single
# hashref (the form the README used to advertise, and the form a caller reaches
# for when marshalling from decoded JSON):
#
#   $client->tool('memory_status');
#   $client->tool('memory_recall', query => 'x', limit => 5);
#   $client->tool('memory_recall', { query => 'x', limit => 5 });
#
# A flat pair list and a hashref must never be mixed; doing so is a bug in the
# caller, not something to silently reinterpret.
sub tool {
    my ($self, $name, @args) = @_;

    Mem20::ValidationError->throw(message => 'tool name is required', tool => '')
        unless defined $name && length $name;

    my $params = _params_from(\@args, "$name");

    $self->_validate($name, $params);

    my $result = $self->_transport->request(
        'tools/call',
        { name => "$name", arguments => $params },
    );

    return $self->_normalize_result($name, $result);
}

sub call_tool { return shift->tool(@_) }

# List the tools the server exposes.
sub tools {
    my ($self) = @_;
    my $listing = $self->_transport->request( q{tools/list}, {} );

    # Cache the schemas alongside the names: tools/list is the only authority
    # on what arguments a tool accepts, so client-side validation reads the
    # live schema instead of a hand-copied table that drifts.
    my @tools = grep { ref $_ eq 'HASH' && defined $_->{name} } @{ $listing->{tools} || [] };
    $self->{tool_names}   = [ map { $_->{name} } @tools ];
    $self->{tool_schemas} = { map { $_->{name} => ( $_->{inputSchema} || {} ) } @tools };

    return $listing;
}

# The names of every registered tool, cached after the first call.
sub tool_names {
    my ($self) = @_;
    return $self->{tool_names} if $self->{tool_names};

    my $listing = $self->tools;
    return $self->{tool_names};
}

# name => inputSchema, for every advertised tool.
sub tool_schemas {
    my ($self) = @_;
    $self->tool_names unless $self->{tool_schemas};    # fills both
    return $self->{tool_schemas} || {};
}

# The inputSchema for one tool, or undef if the server does not advertise it.
sub tool_schema {
    my ($self, $name) = @_;
    return $self->tool_schemas->{$name};
}

# Compare the live surface against the counts this SDK release was compiled
# against. Returns a hashref:
#
#   { ok => 1, tools => 270, expected_tools => 270, domains => 27, ... }
#
# `ok` is false when the live tool count differs, and `missing`/`extra` name the
# tools that moved. Domains are a registration-time figure and cannot be read
# off the wire, so `domains` reports the compiled constant.
sub verify_surface {
    my ($self) = @_;

    my $live = $self->tool_names;

    return {
        ok             => ( @$live == $Mem20::Version::SURFACE_TOOL_COUNT ? 1 : 0 ),
        tools          => scalar @$live,
        expected_tools => $Mem20::Version::SURFACE_TOOL_COUNT,
        domains        => $Mem20::Version::SURFACE_DOMAIN_COUNT,
        server_version => $Mem20::Version::SERVER_VERSION,
    };
}

# The compiled expectation is a count, not a name list: the surface is large and
# upstream adds tools often, so the SDK asserts the size it was built and tested
# against and reports the delta rather than hard-failing on a rename.

# ---------------------------------------------------------- long-running jobs
#
# LLM-backed tools (imagination_*, cog_*, tot_*, beam_search, least_to_most,
# react_reason, theory_of_mind_*, self_model_reflect, memory_auto_consolidate,
# cognitive_substrate) do not answer inline. They return
#
#   {"job_id":"1d68a688ff44","status":"running","tool":"cog_plan",
#    "poll":"job_status","wait":"job_wait"}
#
# as the text payload of a SUCCESSFUL result. A caller that assumes one
# response carries the answer silently gets that JSON instead of an answer.

# Decode a job envelope out of a tool result, or return undef if the result is
# an ordinary answer.
sub job_from {
    my ($self, $result) = @_;
    my $text = $self->text($result);
    return undef unless defined $text && $text =~ /^\s*\{/;

    my $decoded = eval { JSON::PP->new->utf8->decode($text) };
    return undef unless ref $decoded eq 'HASH' && $decoded->{job_id};

    return $decoded;
}

# The tools mem20 answers with a job envelope instead of a result. The list is
# a compiled copy of Mem20MCPServer.LONG_RUNNING_TOOLS (see Mem20::Version);
# it is a literal in the server, not a name pattern, so it cannot be derived.
sub long_running_tools { [ @Mem20::Version::LONG_RUNNING_TOOLS ] }

# True when $name is one of those tools.
sub is_long_running {
    my ($self, $name) = @_;
    return 0 unless defined $name;
    return $Mem20::Version::LONG_RUNNING_TOOL{$name} ? 1 : 0;
}

# The statuses that mean "finished, but there is no result in it". `ok` is the
# only success spelling the server has.
my %JOB_FAILED = map { $_ => 1 } qw(error not_found);

# Poll job_status until the job reaches a terminal state, or the deadline
# passes. Returns the decoded TERMINAL status hashref.
#
# Raises instead of returning whenever there is no result to return:
#
#   Mem20::JobTimeoutError  the deadline passed with the job still running
#   Mem20::JobFailedError   the job ended `error` or `not_found`
#
# Returning the last observed status on timeout would be the job-path twin of
# the isError bug: {"status":"running","result":null} is a truthy hashref with
# no data in it, so `if ($final)` succeeds and ->{result} is undef. The whole
# point of this method is to hand back an answer, so "no answer yet" has to be
# an exception. `timeout => 0` is rejected rather than read as "never time
# out" -- an unbounded poll loop is how a client hangs a cron job forever.
#
# Status vocabulary from mcp/server.py: _spawn_job() starts at 'running',
# _run_job() ends at 'ok' or 'error', _job_status() answers 'not_found' for an
# unknown id. There is no done/complete/finished spelling. pending and queued
# are treated as non-terminal too, so a future server that queues work before
# starting it does not silently become a dropped result.
sub wait_for_job {
    my ($self, $job_id, %opts) = @_;

    Mem20::ValidationError->throw(message => 'job_id is required', tool => 'job_status')
        unless defined $job_id && length $job_id;

    my $timeout  = defined $opts{timeout} ? $opts{timeout} : $self->{config}->timeout;
    my $interval = defined $opts{interval} && $opts{interval} > 0 ? $opts{interval} : 0.25;

    Mem20::ValidationError->throw(
        message => 'wait_for_job timeout must be greater than 0 (an unbounded poll loop cannot be cancelled)',
        tool    => 'job_status',
    ) unless defined $timeout && $timeout =~ /^[0-9.]+$/ && $timeout > 0;

    my $deadline = Time::HiRes::time() + $timeout;
    my $polls    = 0;
    my $last;

    while (1) {
        $polls++;
        my $raw = $self->tool( 'job_status', job_id => "$job_id" );

        $last = $self->_decode_json_text($raw)
            // { status => 'unknown', raw => $self->text($raw) };

        my $status = defined $last->{status} ? "$last->{status}" : '';

        # Success: the only terminal state that carries a result.
        if ( $status eq 'ok' ) {
            # An `ok` with a null result is still a dropped answer. Do not
            # pretend otherwise just because the status word looks good.
            Mem20::JobFailedError->throw(
                message => "job $job_id reported status 'ok' but carried no result",
                job_id  => $job_id,
                status  => $status,
                last    => $last,
            ) if !exists $last->{result} || !defined $last->{result};
            return $last;
        }

        # Terminal failure: surface the server's own error text.
        if ( $JOB_FAILED{$status} ) {
            my $detail = defined $last->{error} ? $last->{error} : '';
            $detail = $last->{raw} // '' if !length $detail && defined $last->{raw};
            Mem20::JobFailedError->throw(
                message => length $detail
                    ? "job $job_id ended '$status': $detail"
                    : "job $job_id ended '$status'",
                job_id => $job_id,
                status => $status,
                last   => $last,
            );
        }

        # Anything else is treated as "not finished yet", including an
        # unrecognised status: guessing that an unknown word means success is
        # how a future server state silently becomes a dropped result.
        my $left = $deadline - Time::HiRes::time();
        if ( $left <= 0 ) {
            Mem20::JobTimeoutError->throw(
                message => "job $job_id never reached a terminal state within ${timeout}s"
                         . " (last status: " . ( length $status ? $status : 'unknown' )
                         . ", polls: $polls)",
                job_id  => $job_id,
                status  => length $status ? $status : 'unknown',
                polls   => $polls,
                timeout => $timeout,
                last    => $last,
            );
        }

        Time::HiRes::sleep( $interval < $left ? $interval : $left );
    }
}

# Call a tool and, when it answers with a job envelope, wait for the real
# result. Use this for the long-running tools; use tool() when you want the
# envelope yourself.
sub call_tool_await {
    my ($self, $name, @args) = @_;

    my %opts;
    if ( @args && ref $args[-1] eq 'HASH' && exists $args[-1]{__await} ) {
        my $tail = pop @args;
        %opts = %{ delete $tail->{__await} };
    }

    my $result = $self->tool( $name, @args );
    my $job    = $self->job_from($result);

    # A long-running tool that answered inline is fine (the server may have
    # completed it synchronously), but a long-running tool that answered with
    # something that is NOT a job envelope is a dropped answer: returning it
    # would hand the caller a status word where a result belongs.
    if ( !$job && $self->is_long_running($name) ) {
        Mem20::JobFailedError->throw(
            message => "$name is a long-running tool but answered without a job envelope"
                     . ' (no job_id in the response)',
            job_id  => undef,
            status  => 'no_envelope',
            last    => $result,
        );
    }

    return $result unless $job;

    my $final = $self->wait_for_job( $job->{job_id}, %opts );
    return $final;
}

# ---------------------------------------------------------- memory primitives

# Store a grounded fact.
#
#   $client->memory_store(
#       content          => 'prod runs build 4127',
#       epistemic_status => 'observed',      # REQUIRED
#       category         => 'project',       # user_pref | project | tool | general
#       tags             => [ 'prod', 'build' ],
#   );
#
# epistemic_status is required by the tool's own inputSchema. Omitting it does
# NOT fail at the protocol level: mem20 answers isError=false and returns an
# explanatory string, which a caller that only checks for exceptions will treat
# as success. That is why this method refuses to send a request without it.
sub memory_store {
    my ($self, %args) = @_;

    Mem20::ValidationError->throw(
        message => 'content is required for memory_store', tool => 'memory_store'
    ) unless defined $args{content};

    Mem20::ValidationError->throw(
        message => 'epistemic_status is required for memory_store; declare how the '
                 . 'claim is known (observed, inferred, user_stated, hypothesis, '
                 . 'agent_generated, unlabeled)',
        tool => 'memory_store',
    ) unless defined $args{epistemic_status} && length $args{epistemic_status};

    my $status = "$args{epistemic_status}";
    if ( $status eq 'imagined' ) {
        Mem20::ValidationError->throw(
            message => "'imagined' is not a grounded epistemic_status: invented content "
                     . 'belongs in the simulated partition. Use memory_simulate_store.',
            tool => 'memory_store',
        );
    }
    if ( !$GROUNDED_EPISTEMIC{$status} ) {
        Mem20::ValidationError->throw(
            message => "unknown epistemic_status '$status' (expected one of: "
                     . join(', ', @GROUNDED_EPISTEMIC) . ')',
            tool => 'memory_store',
        );
    }

    my %payload = (
        content          => $args{content},
        category         => defined $args{category} ? $args{category} : 'general',
        epistemic_status => $status,
    );

    if (defined $args{tags}) {
        $payload{tags} = ref $args{tags} eq 'ARRAY'
            ? join(',', @{ $args{tags} })
            : "$args{tags}";
    }

    return $self->tool( 'memory_store', %payload );
}

# Search stored facts.
sub memory_recall {
    my ($self, %args) = @_;

    Mem20::ValidationError->throw(
        message => 'query is required for memory_recall', tool => 'memory_recall'
    ) unless defined $args{query};

    my %payload = ( query => $args{query} );
    $payload{category} = $args{category} if defined $args{category};
    $payload{limit}    = $args{limit}    if defined $args{limit};

    return $self->tool( 'memory_recall', %payload );
}

# The plain-text payload of a tool-result envelope.
#
# The server returns { content => [ { type => 'text', text => ... }, ... ] },
# but a tool may return a bare string or several parts, so all three shapes are
# accepted rather than making every caller guard.
#
# Callable both as a function and as a method, because the README documented
# `Mem20::Client::text($hits)` and that form used to return an empty string:
#
#   Mem20::Client::text($hits);     # function form
#   $client->text($hits);           # method form
sub text {
    my $self_or_result = shift;

    my $result = @_ ? shift : $self_or_result;

    return '' unless defined $result;
    return "$result" unless ref $result eq 'HASH';

    my $parts = $result->{content};
    return '' unless ref $parts eq 'ARRAY';

    my @texts;
    for my $part (@$parts) {
        next unless ref $part eq 'HASH';
        push @texts, $part->{text} if defined $part->{text};
    }
    return join "\n", @texts;
}

# --------------------------------------------------------- argument validation

# Validate a call against the tool's own advertised inputSchema.
#
# Required arguments are enforced always: mem20 does not enforce them itself for
# most tools (memory_store with no content stores an empty fact and reports
# success), so the client is the only place a missing argument can be caught.
#
# Enum membership is enforced only under `strict`, because the live server
# accepts out-of-enum values that its schema forbids (memory_store accepts
# category="deploys") and turning that into a hard client error would reject
# calls the server honours. memory_store applies its own epistemic rules above
# regardless of this switch.
sub _validate {
    my ($self, $name, $params) = @_;

    return 1 unless $self->{strict};

    my $schema = $self->tool_schema($name);
    return 1 unless ref $schema eq 'HASH';

    my %props = %{ $schema->{properties} || {} };
    for my $required ( @{ $schema->{required} || [] } ) {
        next if exists $params->{$required} && defined $params->{$required};
        Mem20::ValidationError->throw(
            message => "$name requires '$required'",
            tool    => $name,
            params  => $params,
        );
    }

    for my $key (sort keys %props) {
        next unless exists $params->{$key};
        my $enum = $props{$key}{enum};
        next unless ref $enum eq 'ARRAY' && @$enum;

        my $value = $params->{$key};
        next if grep { defined $value && "$_" eq "$value" } @$enum;

        Mem20::ValidationError->throw(
            message => "$name: '$key' must be one of " . join(', ', @$enum)
                     . " (got '$value')",
            tool    => $name,
            params  => $params,
        );
    }
    return 1;
}

# -------------------------------------------------------------- result shaping

# mem20 signals tool failure THREE different ways, and only one of them is a
# JSON-RPC error object:
#
#   1. JSON-RPC error object                -> ToolError (raised in transport)
#   2. result.isError = true                -> ToolError (unknown tool, handler raise)
#   3. isError = false, text starts "Error" -> ToolError with soft_error = 1
#
# Case 3 is the dangerous one: the envelope is a protocol success, so a client
# that trusts `isError` reports a rejected write as a stored fact. Both live
# transcripts are in sdk/perl/AUDIT.md.
sub _normalize_result {
    my ($self, $name, $result) = @_;

    return $result unless ref $result eq 'HASH';

    if ( $result->{isError} ) {
        my $message = $self->text($result);
        $message =~ s/\s+\z//;
        Mem20::ToolError->throw(
            message    => length $message ? $message : "tool '$name' reported isError",
            tool       => $name,
            is_error   => 1,
            data       => $result,
        );
    }

    my $text = $self->text($result);
    if ( defined $text && $text =~ /\A\s*Error\b/ ) {
        my $message = $text;
        $message =~ s/\s+\z//;
        Mem20::ToolError->throw(
            message    => $message,
            tool       => $name,
            is_error   => 0,
            soft_error => 1,
            data       => $result,
        );
    }

    return $result;
}

sub _decode_json_text {
    my ($self, $result) = @_;
    my $text = $self->text($result);
    return undef unless defined $text && length $text;
    my $decoded = eval { JSON::PP->new->utf8->decode($text) };
    return ref $decoded eq 'HASH' ? $decoded : undef;
}

# Turn @args into a JSON object. Accepts a leading hashref or a flat pair list;
# never both.
sub _params_from {
    my ($args, $name) = @_;

    return {} unless @$args;

    if ( ref $args->[0] eq 'HASH' ) {
        Mem20::ValidationError->throw(
            message => "$name: pass either a hashref or a flat key/value list, not both",
            tool    => $name,
        ) if @$args > 1;

        return { %{ $args->[0] } };
    }

    Mem20::ValidationError->throw(
        message => "$name takes named arguments only (got an odd number of values)",
        tool    => $name,
    ) if @$args % 2;

    return { @$args };
}

# --------------------------------------------------------------- health surface

# GET /health -> decoded JSON, or undef when the endpoint is not answering.
sub health {
    my ($self) = @_;
    my $body = eval { $self->_http_get('/health') };
    return $@ ? undef : $body;
}

# GET /ready -> decoded JSON, or undef when the endpoint is not answering.
sub ready {
    my ($self) = @_;
    my $body = eval { $self->_http_get('/ready') };
    return $@ ? undef : $body;
}

# True when GET :port/health answers with a 2xx status.
sub healthy {
    my ($self) = @_;
    my $url = $self->{config}->health_url . '/health';
    my $res = eval { $self->{http}->get($url) };
    return 0 if !$res;
    return $res->{success} ? 1 : 0;
}

# Decoded counters from GET :port/metrics.
sub metrics {
    my ($self) = @_;
    return $self->_http_get('/metrics');
}

sub close {
    my ($self) = @_;
    if ($self->{transport}) {
        $self->{transport}->close;
        $self->{transport} = undef;
    }
    $self->{tool_names}   = undef;
    $self->{tool_schemas} = undef;
    return;
}

sub shutdown { return $_[0]->close }

# ----------------------------------------------------------- dynamic dispatch

# Any tool the server registers can be called as a method:
#
#   $client->memory_status;
#   $client->cog_plan(goal => 'ship 3.0');
#
# Restricted to names the server actually advertises, so a typo fails loudly
# instead of silently doing nothing.
#
# AUTOLOAD is used rather than overriding can(): `can` is consulted by perl
# itself while resolving a method call, and a `can` that advertises a name
# without an AUTOLOAD to back it returns true and then dies "Can't locate
# object method". Advertising and dispatch have to come from the same place.
sub AUTOLOAD {
    my ($self, @args) = @_;

    my $name = our $AUTOLOAD;
    $name =~ s/.*:://;

    return if $name eq 'DESTROY';

    if ( !$self->_callable_tool($name) ) {
        Mem20::ConfigurationError->throw(
            message => "unknown mem20 tool '$name' (the server did not advertise it)"
        );
    }

    return $self->tool( $name, @args );
}

# True only for tools the server actually advertises.
sub _callable_tool {
    my ($self, $name) = @_;

    return 0 if !defined $name || !length $name;
    return 0 if !ref $self;    # called as a class method, not an instance

    my $known = eval { $self->tool_names };
    return 0 if !$known;

    my %known = map { $_ => 1 } @$known;
    return $known{$name} ? 1 : 0;
}

# Complement of the AUTOLOAD above, so `$client->can('memory_status')` is true
# for advertised tools and false otherwise -- checked against the server's own
# list rather than assumed.
sub can {
    my ( $self, $name ) = @_;

    my $installed = UNIVERSAL::can( __PACKAGE__, $name );
    return $installed if $installed;

    return undef if !ref $self || !blessed($self) || !$self->isa(__PACKAGE__);
    return undef if !defined $name;

    # AUTOLOAD backs every advertised tool with the same sub.
    return undef if !$self->_callable_tool($name);
    return \&AUTOLOAD;
}

# ---------------------------------------------------------------- internals

sub _http_get {
    my ($self, $path) = @_;

    my $url = $self->{config}->health_url . $path;
    my $res = $self->{http}->get($url);

    if (!$res->{success}) {
        my $why = $res->{status} ? "HTTP $res->{status}" : ( $res->{content} || 'no response' );
        Mem20::TransportError->throw(message => "could not read $url: $why");
    }

    my $decoded = eval { JSON::PP->new->utf8->decode( $res->{content} ) };
    if ($@) {
        my $why = $@;
        chomp $why;
        Mem20::TransportError->throw(message => "could not decode $url: $why");
    }
    return $decoded;
}

1;
__END__

=head1 NAME

Mem20::Client - facade over the mem20 tool surface

=head1 SYNOPSIS

    use Mem20;
    use Mem20::Client;

    my $client = Mem20::Client->new;
    $client->connect;

    $client->memory_store(
        content          => 'the sky is blue',
        category         => 'general',
        epistemic_status => 'observed',
    );
    my $out = $client->memory_recall(query => 'sky', limit => 5);
    print $client->text($out), "\n";

    $client->memory_status;                  # any registered tool
    $client->close;

=head1 DESCRIPTION

C<tool> reaches every tool the server registers. The named accessors cover the
memory primitives; dynamic dispatch covers everything else, so new server tools
do not need SDK changes.

=head1 METHODS

=over 4

=item C<< new(%options) >> - takes C<config =E<gt> $cfg>, C<< strict =E<gt> 1 >>,
or the same options C<Mem20::Config> accepts.

=item C<connect> - start the child server and complete the MCP handshake. Idempotent.

=item C<< tool($name, @args) >> - call any tool. C<@args> is a flat key/value
list or a single hashref. Alias: C<call_tool>.

=item C<tools> - the raw C<tools/list> result.

=item C<tool_names>, C<tool_schemas>, C<< tool_schema($name) >> - the server's
advertisement, cached after the first call.

=item C<verify_surface> - compare the live tool count with the count this SDK
was built against (270 across 27 domains). Returns C<ok>, C<tools>,
C<expected_tools>, C<domains>, C<server_version>.

=item C<< memory_store(%args) >> - store a grounded fact. C<content> and
C<epistemic_status> are required; C<category> is one of C<user_pref>,
C<project>, C<tool>, C<general>.

=item C<< memory_recall(%args) >> - search stored facts. C<query> required.

=item C<< text($result) >> - flatten a tool-result envelope to plain text.
Callable as a function or a method.

=item C<< job_from($result) >> - decode a background-job envelope, or undef.

=item C<long_running_tools> - arrayref of the 24 tools mem20 answers with a job
envelope instead of a result. The list is a compiled copy of
C<Mem20MCPServer.LONG_RUNNING_TOOLS> from F<mcp/server.py>; it is a literal
there, not a name pattern, so it cannot be derived from tool names
(C<cog_working_memory> is a C<cog_*> tool that answers inline, and
C<beam_search> / C<least_to_most> carry no prefix at all).

=item C<< is_long_running($name) >> - true when C<$name> is one of those 24.

=item C<< wait_for_job($job_id, %opts) >> - poll C<job_status> until the job
reaches a terminal state. Returns the terminal status hashref and B<never> a
still-running one: it raises C<Mem20::JobTimeoutError> if C<timeout> passes
with the job unfinished, and C<Mem20::JobFailedError> if the job ended C<error>
or C<not_found> (or reported C<ok> with a null result). C<timeout> must be
greater than 0.

=item C<< call_tool_await($name, @args) >> - call a tool and, if it returns a
job envelope, wait for the real result. Also raises C<Mem20::JobFailedError>
when C<$name> is long-running but the response carries no C<job_id>, because
that is a status word where a result belongs.

=item C<health>, C<ready>, C<healthy>, C<metrics> - the HTTP health surface.

=item C<close> / C<shutdown> - stop the child and release the transport.

=back

=head1 DYNAMIC DISPATCH

Any advertised tool is callable by name and returns a coderef from C<can>, so
C<< $client->can('memory_status') >> is true only when the server really
offers it.

=head1 FAILURE SHAPES

mem20 reports a failed tool call in more than one way. An unknown I<tool> and a
handler exception arrive as a protocol B<success> with C<result.isError> set; a
tool-internal rejection (a bad C<epistemic_status>, for instance) arrives with
C<result.isError> B<false> and an C<Error ...> text payload. Both raise
C<Mem20::ToolError>; the second sets C<< ->soft_error >>. See
F<sdk/perl/AUDIT.md>.

=head1 LONG-RUNNING TOOLS

LLM-backed tools (24 of them: C<cog_*>, C<imagination_*>, C<tot_*>,
C<beam_search>, C<least_to_most>, C<react_reason>, C<theory_of_mind_*>,
C<self_model_reflect>, C<memory_auto_consolidate>, C<cognitive_substrate>)
answer with a job envelope -- C<{"job_id":...,"status":"running"}> -- as the
text of a B<successful> result, so the answer is not in the response. Use
C<call_tool_await> for those, or C<wait_for_job> on the C<job_id>.
C<long_running_tools> returns the exact set.

The envelope is not an answer and this SDK does not treat it as one:

    my $final = eval { $client->call_tool_await(cog_plan => (goal => 'x')) };
    if (my $err = $@) {
        if (ref $err && $err->isa('Mem20::JobTimeoutError')) { warn "still running\n" }
        if (ref $err && $err->isa('Mem20::JobFailedError'))  { warn "$err\n" }
    }
    else { print $final->{result} }

Status vocabulary is the server's: C<running> while going, C<ok> when there is a
result, C<error> when the job raised, C<not_found> when the id is unknown.

=cut
