package Mem20::Surface;
use strict;
use warnings;

# GENERATED FILE -- DO NOT EDIT BY HAND.
#
# Regenerate with:  perl xt/gen-surface.pl
# Verify in CI:     perl xt/gen-surface.pl --check
#
# Source of truth:
#   docs/surface.json        (live tools/list, cross-checked against the AST)
#   web/src/data/tools.json  (one record per tool: name, domain, module)
#
# Both are produced by scripts/surface_manifest.py in the mem20 repository. The
# generator refuses to emit unless the two agree, so this module cannot encode
# a disagreement between the live server and the source tree.
#
# Why a generated module instead of a runtime JSON read: the SDK installs with
# nothing but core Perl and must not depend on a checkout being present. Baking
# the names in keeps that promise while still letting verify_surface() name the
# exact tools that moved, which a bare integer count cannot do.

our $VERSION = '0.3.0';

# The surface this SDK release was generated against.
our $TOOL_COUNT   = 527;
our $DOMAIN_COUNT = 135;

# Every tool name the server advertises, sorted. Sorted so a diff of this file
# shows additions and removals rather than reshuffling.
our @TOOL_NAMES = qw(
    a2a_call a2a_discover a2a_history a2a_list a2a_orchestrate
    affective_add_goal affective_evaluate affective_get_state
    affective_set_emotion affective_set_value affective_update_preference
    agentz_ground agentz_review agentz_run agentz_status
    alternativedatabaseplaygroundz_status ambientdevicecompanionz_status
    ambientteamradioz_status architecturesimulationsandboxz_status
    assetremixstudioz_status asynccollaborationcapsulesz_status
    audiovoiceandmusicpipelinez_doctor audiovoiceandmusicpipelinez_master
    audiovoiceandmusicpipelinez_mix audiovoiceandmusicpipelinez_status
    autonomousdealdeskz_doctor autonomousdealdeskz_price
    autonomousdealdeskz_status autonomousmicrosaasfoundryz_doctor
    autonomousmicrosaasfoundryz_status autonomousrecoverydirectorz_doctor
    autonomousrecoverydirectorz_status autonomoussaleslaboratoryz_doctor
    autonomoussaleslaboratoryz_status autonomoussoftwarefoundryz_doctor
    autonomoussoftwarefoundryz_status autonomoustrafficcontrollerz_status
    autonomousworkcellsz_doctor autonomousworkcellsz_status
    batteryawareagentschedulerz_status beam_search blender_add_material
    blender_clear_scene blender_create_object blender_export_glb blender_render
    blender_run_bpy blender_set_camera braid_hash braid_head braid_intent_submit
    braid_intent_view braid_prove braid_read braid_sign braid_status braid_write
    businessmodelsimulatorz_doctor businessmodelsimulatorz_status
    causalroutingbrainz_doctor causalroutingbrainz_status cloud_aws_ec2
    cloud_aws_lambda cloud_aws_s3 cloud_azure_blob cloud_cloudflare_worker
    cloud_digitalocean_droplet cloud_docker cloud_gcp_storage cloud_heroku
    cloud_k8s cloudstorage_copy cloudstorage_delete cloudstorage_download
    cloudstorage_list cloudstorage_metadata cloudstorage_presigned_url
    cloudstorage_sync cloudstorage_upload cog_chain cog_plan cog_process
    cog_reason cog_reflect cog_working_memory cognitive_substrate
    collectivemodelintelligencez_doctor collectivemodelintelligencez_status
    comm_calendar_invite comm_contact_manage comm_discord_message
    comm_push_notify comm_read_email comm_send_email comm_slack_message
    comm_sms_send comm_telegram_message communitychallengeenginez_doctor
    communitychallengeenginez_status compoundingproductecosystemz_doctor
    compoundingproductecosystemz_status contextcompressionforgez_doctor
    contextcompressionforgez_status corez_evaluate corez_infer corez_quantize
    corez_wiring corrigibility_capability_tier corrigibility_shutdown
    counterfactualmemorysimulatorz_doctor counterfactualmemorysimulatorz_status
    crdtcollaborationenginez_status crewz_govern crewz_ground crewz_guard
    crewz_status crossplatformmicrokernelz_doctor
    crossplatformmicrokernelz_status crossproductloyaltygraphz_doctor
    crossproductloyaltygraphz_status customerdigitaltwinlabz_doctor
    customerdigitaltwinlabz_status customerlifecycleenginez_doctor
    customerlifecycleenginez_status datalocalityoptimizerz_doctor
    datalocalityoptimizerz_status db_backup db_create_table db_delete db_insert
    db_list_tables db_mongo_find db_query db_redis_command db_schema db_update
    design_asset_optimize design_color_palette design_figma design_image_edit
    design_image_generate design_svg_generate design_typography
    design_ui_component deterministicconfigurationgraphz_doctor
    deterministicconfigurationgraphz_status dev_api_test dev_dependency_analyze
    dev_execute_bash dev_execute_js dev_execute_python dev_format_python
    dev_lint_python dev_run_tests dev_search_code
    devicecapabilitycompilerz_doctor devicecapabilitycompilerz_status
    dreamz_estate dreamz_gate dreamz_ground dreamz_status
    dynamicnarrativeenginez_doctor dynamicnarrativeenginez_status
    dynamicphasereplannerz_status dynamicquestrewardcomposerz_doctor
    dynamicquestrewardcomposerz_status dynamicskillgraphz_doctor
    dynamicskillgraphz_status edgefleet_dispatch edgefleet_doctor
    edgefleet_node_register edgefleet_nodes_list edgefleet_predict
    edgefleet_simulate edgefleet_status edgefleet_workload_submit fin_budget
    fin_crypto_price fin_expense_track fin_financial_news fin_invoice
    fin_portfolio fin_stock_quote fin_tax_calc fs_archive_create
    fs_archive_extract fs_diff fs_disk_usage fs_list fs_metadata fs_permissions
    fs_read fs_read_advanced fs_search fs_watch fs_write fs_write_advanced
    gateway_admission gateway_provenance gateway_translate
    get_cognitive_tree_state graph_execute_reversible_plan imagination_concept
    imagination_counterfactual imagination_critique imagination_dream
    imagination_model imagination_prototype imagination_recombine
    imagination_simulate imagination_visualize irc_join irc_read irc_say
    irc_status irc_who job_status job_wait kilnz_budget kilnz_gate kilnz_ground
    kilnz_status lattice_emit lattice_recall lattice_report lattice_search
    lattice_verify least_to_most lie_acknowledge_cue lie_dual_acknowledge
    lie_feed_audio lie_feed_transcript lie_get_cues lie_list_sessions
    lie_seal_session lie_set_baseline lie_start_session lie_status
    mem20assistz_doctor mem20assistz_status mem20schoolz_create_course
    mem20schoolz_create_exam mem20schoolz_create_learning_path
    mem20schoolz_doctor mem20schoolz_evaluate_task mem20schoolz_get_lesson
    mem20schoolz_issue_credential mem20schoolz_list_courses
    mem20schoolz_list_exams mem20schoolz_log_session mem20schoolz_mentor_match
    mem20schoolz_mentorship_hours mem20schoolz_progression_plan
    mem20schoolz_register_mentor mem20schoolz_skill_level mem20schoolz_status
    mem20schoolz_take_exam mem20schoolz_track_progress
    mem20schoolz_verify_credential memory_assess_confidence
    memory_audit_contamination memory_auto_consolidate memory_backfill_labels
    memory_cluster memory_consolidate memory_context_window memory_contradict
    memory_decay memory_deduplicate memory_detect_gaps memory_engine_guard
    memory_engine_health memory_engine_namespace memory_engine_recall
    memory_engine_subsystem memory_engine_veto memory_entity_extract
    memory_epistemic_veto memory_export memory_feedback memory_get_pinned_block
    memory_graph_traverse memory_import memory_index_health memory_ingest_audio
    memory_ingest_code memory_ingest_image memory_ingest_pdf
    memory_label_coverage memory_list_pinned_blocks memory_list_simulated
    memory_mood_tag memory_namespace_create memory_namespace_list
    memory_pin_block memory_probe memory_promote memory_quarantine_simulated
    memory_reason memory_recall memory_recall_graph memory_recall_hybrid
    memory_recall_semantic memory_reinforce memory_related memory_scan_pii
    memory_self_audit memory_set_epistemic_status memory_shared_recall
    memory_shared_store memory_simulate_store memory_stats memory_status
    memory_store memory_timeline memory_triggers memory_unpin_block
    milestoneriskpredictorz_status mkt_ab_test mkt_analytics
    mkt_competitor_analysis mkt_content_generate mkt_email_campaign
    mkt_hashtag_research mkt_seo_analyze mkt_social_analytics mkt_social_post
    offerassemblyfabricz_doctor offerassemblyfabricz_status
    offergenomeenginez_doctor offergenomeenginez_status opportunityradarz_doctor
    opportunityradarz_status ops_cli_audit ops_registry ops_wiring
    outcomesimulationlabz_doctor outcomesimulationlabz_status
    personalautomationcanvasz_doctor personalautomationcanvasz_status
    personalcognitivesearchz_doctor personalcognitivesearchz_status
    personalmodelevolutionz_doctor personalmodelevolutionz_status
    personalworkflowtwinz_doctor personalworkflowtwinz_status pipelinez_doctor
    pipelinez_status planetarybatchfabricz_doctor planetarybatchfabricz_status
    playermotivationtwinz_doctor playermotivationtwinz_status
    predictiverecallenginez_doctor predictiverecallenginez_status
    prioritycollisionresolverz_status procedural_add_skill
    procedural_execute_skill procedural_find_skills procedural_get_skill
    procedural_learn procedural_list_skills prod_goal_set prod_habit_track
    prod_meeting_notes prod_note_create prod_note_search prod_project_create
    prod_task_create prod_task_list prod_task_update prod_time_track
    productionplanningandtaskorchestrationpipelinez_doctor
    productionplanningandtaskorchestrationpipelinez_status
    productledgrowthsimulatorz_doctor productledgrowthsimulatorz_status
    protocolautodiscoveryenginez_doctor protocolautodiscoveryenginez_status
    react_reason realitytosoftwarecompilerz_doctor
    realitytosoftwarecompilerz_status realtimebusinesstwinz_doctor
    realtimebusinesstwinz_status realtimeeventautopilotz_doctor
    realtimeeventautopilotz_status realtimeteampresencez_doctor
    realtimeteampresencez_status realworldimpactrewardsz_doctor
    realworldimpactrewardsz_status reflexion remoteexperimentlabz_doctor
    remoteexperimentlabz_status resourceexchangemarketz_doctor
    resourceexchangemarketz_status revenueleakhunterz_doctor
    revenueleakhunterz_status rewardforgez_doctor rewardforgez_status
    rigginganimationandmotionpipelinez_doctor
    rigginganimationandmotionpipelinez_status roadmap_create roadmap_get
    roadmap_list roadmap_update_phase roamingworkloadschedulerz_doctor
    roamingworkloadschedulerz_status runtimecompatibilityenginez_doctor
    runtimecompatibilityenginez_status runtimepromptoptimizerz_doctor
    runtimepromptoptimizerz_status scrape_api scrape_dynamic scrape_forms
    scrape_page scrape_rss scrape_sitemap scrape_structured scrape_submit_form
    search_academic search_code search_images search_knowledge_base search_local
    search_news search_web secretslessworkloadidentityz_doctor
    secretslessworkloadidentityz_status securecomputecapsulesz_doctor
    securecomputecapsulesz_status self_model_create self_model_get
    self_model_reflect selfhealingplansz_doctor selfhealingplansz_status
    selfoptimizingkernelz_doctor selfoptimizingkernelz_status
    selftuningresourcegovernorz_doctor selftuningresourcegovernorz_status
    selfz_doctor selfz_status sensorymemoryingestz_doctor
    sensorymemoryingestz_status servicebundlingenginez_doctor
    servicebundlingenginez_status simz_doctor simz_status
    skillbasedprogressionbrainz_doctor skillbasedprogressionbrainz_status
    skillmemorytransferz_doctor skillmemorytransferz_status
    spatialcommanduniversez_doctor spatialcommanduniversez_status
    specialistmodelforgez_doctor specialistmodelforgez_status
    speculativeworkflowenginez_doctor speculativeworkflowenginez_status
    stream_publish stream_recall stream_report stream_search stream_verify
    studioz_doctor studioz_status styleguideagentz_doctor
    styleguideagentz_status syntheticevaluatorarenaz_doctor
    syntheticevaluatorarenaz_status temporal_doctor temporal_get temporal_ingest
    temporal_put temporal_slices theory_of_mind_perspective
    theory_of_mind_simulate toolchest_inventory toolchest_wiring tot_diagnose
    tot_modeling tot_reason twinz_doctor twinz_status
    uniteconomicsautopilotz_doctor uniteconomicsautopilotz_status
    unity_build_project unity_create_script unity_generate_asmdef unity_run_test
    unity_validate_project universalhealthnervoussystemz_doctor
    universalhealthnervoussystemz_status universalintegrationcompilerz_doctor
    universalintegrationcompilerz_status vcs_asset_release_audit vcs_git_blame
    vcs_git_branch vcs_git_commit vcs_git_diff vcs_git_log vcs_git_remote
    vcs_git_stash vcs_git_status vcs_git_tag vcs_github_issue vcs_github_pr
    verify_drift verify_lint verify_tests verify_wiring
    visualagentblackboardz_doctor visualagentblackboardz_status
    visualdataflowcomposerz_doctor visualdataflowcomposerz_status
    webhook_deliver webhook_doctor webhook_replay webhook_route_capabilities
    webhook_verify world_model_add_rule world_model_add_variable
    world_model_get_state world_model_predict world_model_record_prediction
    world_model_reset world_model_resolve_prediction world_model_simulate
    zerodowntimemigrationbrainz_status zerotouchnodeswarmz_doctor
    zerotouchnodeswarmz_status

);

# Tool name => owning domain, as declared by the tool's module in the AST
# catalog. This is the registration-time domain, not a prefix bucket: memory_*
# and vault_* are separate prefixes inside one domain, and a bare `reflexion`
# has no underscore at all.
our %TOOL_DOMAIN = (
    'a2a_call'                                   => 'a2a',
    'a2a_discover'                               => 'a2a',
    'a2a_history'                                => 'a2a',
    'a2a_list'                                   => 'a2a',
    'a2a_orchestrate'                            => 'a2a',
    'affective_add_goal'                         => 'world',
    'affective_evaluate'                         => 'world',
    'affective_get_state'                        => 'world',
    'affective_set_emotion'                      => 'world',
    'affective_set_value'                        => 'world',
    'affective_update_preference'                => 'world',
    'agentz_ground'                              => 'agentz',
    'agentz_review'                              => 'agentz',
    'agentz_run'                                 => 'agentz',
    'agentz_status'                              => 'agentz',
    'alternativedatabaseplaygroundz_status'      => 'mem20alternativedatabaseplaygroundz',
    'ambientdevicecompanionz_status'             => 'mem20ambientdevicecompanionz',
    'ambientteamradioz_status'                   => 'mem20ambientteamradioz',
    'architecturesimulationsandboxz_status'      => 'mem20architecturesimulationsandboxz',
    'assetremixstudioz_status'                   => 'mem20assetremixstudioz',
    'asynccollaborationcapsulesz_status'         => 'mem20asynccollaborationcapsulesz',
    'audiovoiceandmusicpipelinez_doctor'         => 'mem20audiovoiceandmusicpipelinez',
    'audiovoiceandmusicpipelinez_master'         => 'mem20audiovoiceandmusicpipelinez',
    'audiovoiceandmusicpipelinez_mix'            => 'mem20audiovoiceandmusicpipelinez',
    'audiovoiceandmusicpipelinez_status'         => 'mem20audiovoiceandmusicpipelinez',
    'autonomousdealdeskz_doctor'                 => 'mem20autonomousdealdeskz',
    'autonomousdealdeskz_price'                  => 'mem20autonomousdealdeskz',
    'autonomousdealdeskz_status'                 => 'mem20autonomousdealdeskz',
    'autonomousmicrosaasfoundryz_doctor'         => 'mem20autonomousmicrosaasfoundryz',
    'autonomousmicrosaasfoundryz_status'         => 'mem20autonomousmicrosaasfoundryz',
    'autonomousrecoverydirectorz_doctor'         => 'mem20autonomousrecoverydirectorz',
    'autonomousrecoverydirectorz_status'         => 'mem20autonomousrecoverydirectorz',
    'autonomoussaleslaboratoryz_doctor'          => 'mem20autonomoussaleslaboratoryz',
    'autonomoussaleslaboratoryz_status'          => 'mem20autonomoussaleslaboratoryz',
    'autonomoussoftwarefoundryz_doctor'          => 'mem20autonomoussoftwarefoundryz',
    'autonomoussoftwarefoundryz_status'          => 'mem20autonomoussoftwarefoundryz',
    'autonomoustrafficcontrollerz_status'        => 'mem20autonomoustrafficcontrollerz',
    'autonomousworkcellsz_doctor'                => 'mem20autonomousworkcellsz',
    'autonomousworkcellsz_status'                => 'mem20autonomousworkcellsz',
    'batteryawareagentschedulerz_status'         => 'mem20batteryawareagentschedulerz',
    'beam_search'                                => 'thought_process',
    'blender_add_material'                       => 'blender',
    'blender_clear_scene'                        => 'blender',
    'blender_create_object'                      => 'blender',
    'blender_export_glb'                         => 'blender',
    'blender_render'                             => 'blender',
    'blender_run_bpy'                            => 'blender',
    'blender_set_camera'                         => 'blender',
    'braid_hash'                                 => 'braid',
    'braid_head'                                 => 'braid',
    'braid_intent_submit'                        => 'braid',
    'braid_intent_view'                          => 'braid',
    'braid_prove'                                => 'braid',
    'braid_read'                                 => 'braid',
    'braid_sign'                                 => 'braid',
    'braid_status'                               => 'braid',
    'braid_write'                                => 'braid',
    'businessmodelsimulatorz_doctor'             => 'mem20businessmodelsimulatorz',
    'businessmodelsimulatorz_status'             => 'mem20businessmodelsimulatorz',
    'causalroutingbrainz_doctor'                 => 'mem20causalroutingbrainz',
    'causalroutingbrainz_status'                 => 'mem20causalroutingbrainz',
    'cloud_aws_ec2'                              => 'cloudservice',
    'cloud_aws_lambda'                           => 'cloudservice',
    'cloud_aws_s3'                               => 'cloudservice',
    'cloud_azure_blob'                           => 'cloudservice',
    'cloud_cloudflare_worker'                    => 'cloudservice',
    'cloud_digitalocean_droplet'                 => 'cloudservice',
    'cloud_docker'                               => 'cloudservice',
    'cloud_gcp_storage'                          => 'cloudservice',
    'cloud_heroku'                               => 'cloudservice',
    'cloud_k8s'                                  => 'cloudservice',
    'cloudstorage_copy'                          => 'cloudstorage',
    'cloudstorage_delete'                        => 'cloudstorage',
    'cloudstorage_download'                      => 'cloudstorage',
    'cloudstorage_list'                          => 'cloudstorage',
    'cloudstorage_metadata'                      => 'cloudstorage',
    'cloudstorage_presigned_url'                 => 'cloudstorage',
    'cloudstorage_sync'                          => 'cloudstorage',
    'cloudstorage_upload'                        => 'cloudstorage',
    'cog_chain'                                  => 'cognitive',
    'cog_plan'                                   => 'cognitive',
    'cog_process'                                => 'cognitive',
    'cog_reason'                                 => 'cognitive',
    'cog_reflect'                                => 'cognitive',
    'cog_working_memory'                         => 'cognitive',
    'cognitive_substrate'                        => 'thought_process',
    'collectivemodelintelligencez_doctor'        => 'mem20collectivemodelintelligencez',
    'collectivemodelintelligencez_status'        => 'mem20collectivemodelintelligencez',
    'comm_calendar_invite'                       => 'communication',
    'comm_contact_manage'                        => 'communication',
    'comm_discord_message'                       => 'communication',
    'comm_push_notify'                           => 'communication',
    'comm_read_email'                            => 'communication',
    'comm_send_email'                            => 'communication',
    'comm_slack_message'                         => 'communication',
    'comm_sms_send'                              => 'communication',
    'comm_telegram_message'                      => 'communication',
    'communitychallengeenginez_doctor'           => 'mem20communitychallengeenginez',
    'communitychallengeenginez_status'           => 'mem20communitychallengeenginez',
    'compoundingproductecosystemz_doctor'        => 'mem20compoundingproductecosystemz',
    'compoundingproductecosystemz_status'        => 'mem20compoundingproductecosystemz',
    'contextcompressionforgez_doctor'            => 'mem20contextcompressionforgez',
    'contextcompressionforgez_status'            => 'mem20contextcompressionforgez',
    'corez_evaluate'                             => 'corez',
    'corez_infer'                                => 'corez',
    'corez_quantize'                             => 'corez',
    'corez_wiring'                               => 'corez',
    'corrigibility_capability_tier'              => 'cognitive',
    'corrigibility_shutdown'                     => 'cognitive',
    'counterfactualmemorysimulatorz_doctor'      => 'mem20counterfactualmemorysimulatorz',
    'counterfactualmemorysimulatorz_status'      => 'mem20counterfactualmemorysimulatorz',
    'crdtcollaborationenginez_status'            => 'mem20crdtcollaborationenginez',
    'crewz_govern'                               => 'crewz',
    'crewz_ground'                               => 'crewz',
    'crewz_guard'                                => 'crewz',
    'crewz_status'                               => 'crewz',
    'crossplatformmicrokernelz_doctor'           => 'mem20crossplatformmicrokernelz',
    'crossplatformmicrokernelz_status'           => 'mem20crossplatformmicrokernelz',
    'crossproductloyaltygraphz_doctor'           => 'mem20crossproductloyaltygraphz',
    'crossproductloyaltygraphz_status'           => 'mem20crossproductloyaltygraphz',
    'customerdigitaltwinlabz_doctor'             => 'mem20customerdigitaltwinlabz',
    'customerdigitaltwinlabz_status'             => 'mem20customerdigitaltwinlabz',
    'customerlifecycleenginez_doctor'            => 'mem20customerlifecycleenginez',
    'customerlifecycleenginez_status'            => 'mem20customerlifecycleenginez',
    'datalocalityoptimizerz_doctor'              => 'mem20datalocalityoptimizerz',
    'datalocalityoptimizerz_status'              => 'mem20datalocalityoptimizerz',
    'db_backup'                                  => 'database',
    'db_create_table'                            => 'database',
    'db_delete'                                  => 'database',
    'db_insert'                                  => 'database',
    'db_list_tables'                             => 'database',
    'db_mongo_find'                              => 'database',
    'db_query'                                   => 'database',
    'db_redis_command'                           => 'database',
    'db_schema'                                  => 'database',
    'db_update'                                  => 'database',
    'design_asset_optimize'                      => 'design',
    'design_color_palette'                       => 'design',
    'design_figma'                               => 'design',
    'design_image_edit'                          => 'design',
    'design_image_generate'                      => 'design',
    'design_svg_generate'                        => 'design',
    'design_typography'                          => 'design',
    'design_ui_component'                        => 'design',
    'deterministicconfigurationgraphz_doctor'    => 'mem20deterministicconfigurationgraphz',
    'deterministicconfigurationgraphz_status'    => 'mem20deterministicconfigurationgraphz',
    'dev_api_test'                               => 'dev',
    'dev_dependency_analyze'                     => 'dev',
    'dev_execute_bash'                           => 'dev',
    'dev_execute_js'                             => 'dev',
    'dev_execute_python'                         => 'dev',
    'dev_format_python'                          => 'dev',
    'dev_lint_python'                            => 'dev',
    'dev_run_tests'                              => 'dev',
    'dev_search_code'                            => 'dev',
    'devicecapabilitycompilerz_doctor'           => 'mem20devicecapabilitycompilerz',
    'devicecapabilitycompilerz_status'           => 'mem20devicecapabilitycompilerz',
    'dreamz_estate'                              => 'dreamz',
    'dreamz_gate'                                => 'dreamz',
    'dreamz_ground'                              => 'dreamz',
    'dreamz_status'                              => 'dreamz',
    'dynamicnarrativeenginez_doctor'             => 'mem20dynamicnarrativeenginez',
    'dynamicnarrativeenginez_status'             => 'mem20dynamicnarrativeenginez',
    'dynamicphasereplannerz_status'              => 'mem20dynamicphasereplannerz',
    'dynamicquestrewardcomposerz_doctor'         => 'mem20dynamicquestrewardcomposerz',
    'dynamicquestrewardcomposerz_status'         => 'mem20dynamicquestrewardcomposerz',
    'dynamicskillgraphz_doctor'                  => 'mem20dynamicskillgraphz',
    'dynamicskillgraphz_status'                  => 'mem20dynamicskillgraphz',
    'edgefleet_dispatch'                         => 'edgefleet',
    'edgefleet_doctor'                           => 'edgefleet',
    'edgefleet_node_register'                    => 'edgefleet',
    'edgefleet_nodes_list'                       => 'edgefleet',
    'edgefleet_predict'                          => 'edgefleet',
    'edgefleet_simulate'                         => 'edgefleet',
    'edgefleet_status'                           => 'edgefleet',
    'edgefleet_workload_submit'                  => 'edgefleet',
    'fin_budget'                                 => 'finance',
    'fin_crypto_price'                           => 'finance',
    'fin_expense_track'                          => 'finance',
    'fin_financial_news'                         => 'finance',
    'fin_invoice'                                => 'finance',
    'fin_portfolio'                              => 'finance',
    'fin_stock_quote'                            => 'finance',
    'fin_tax_calc'                               => 'finance',
    'fs_archive_create'                          => 'filesystem',
    'fs_archive_extract'                         => 'filesystem',
    'fs_diff'                                    => 'filesystem',
    'fs_disk_usage'                              => 'filesystem',
    'fs_list'                                    => 'integration',
    'fs_metadata'                                => 'filesystem',
    'fs_permissions'                             => 'filesystem',
    'fs_read'                                    => 'integration',
    'fs_read_advanced'                           => 'filesystem',
    'fs_search'                                  => 'filesystem',
    'fs_watch'                                   => 'filesystem',
    'fs_write'                                   => 'integration',
    'fs_write_advanced'                          => 'filesystem',
    'gateway_admission'                          => 'shapeshift',
    'gateway_provenance'                         => 'shapeshift',
    'gateway_translate'                          => 'shapeshift',
    'get_cognitive_tree_state'                   => 'thought_process',
    'graph_execute_reversible_plan'              => 'rm052',
    'imagination_concept'                        => 'cognitive',
    'imagination_counterfactual'                 => 'cognitive',
    'imagination_critique'                       => 'cognitive',
    'imagination_dream'                          => 'cognitive',
    'imagination_model'                          => 'cognitive',
    'imagination_prototype'                      => 'cognitive',
    'imagination_recombine'                      => 'cognitive',
    'imagination_simulate'                       => 'cognitive',
    'imagination_visualize'                      => 'cognitive',
    'irc_join'                                   => 'irc',
    'irc_read'                                   => 'irc',
    'irc_say'                                    => 'irc',
    'irc_status'                                 => 'irc',
    'irc_who'                                    => 'irc',
    'job_status'                                 => 'job',
    'job_wait'                                   => 'job',
    'kilnz_budget'                               => 'kilnz',
    'kilnz_gate'                                 => 'kilnz',
    'kilnz_ground'                               => 'kilnz',
    'kilnz_status'                               => 'kilnz',
    'lattice_emit'                               => 'lattice',
    'lattice_recall'                             => 'lattice',
    'lattice_report'                             => 'lattice',
    'lattice_search'                             => 'lattice',
    'lattice_verify'                             => 'lattice',
    'least_to_most'                              => 'thought_process',
    'lie_acknowledge_cue'                        => 'lie',
    'lie_dual_acknowledge'                       => 'lie',
    'lie_feed_audio'                             => 'lie',
    'lie_feed_transcript'                        => 'lie',
    'lie_get_cues'                               => 'lie',
    'lie_list_sessions'                          => 'lie',
    'lie_seal_session'                           => 'lie',
    'lie_set_baseline'                           => 'lie',
    'lie_start_session'                          => 'lie',
    'lie_status'                                 => 'lie',
    'mem20assistz_doctor'                        => 'mem20assistz',
    'mem20assistz_status'                        => 'mem20assistz',
    'mem20schoolz_create_course'                 => 'mem20schoolz',
    'mem20schoolz_create_exam'                   => 'mem20schoolz',
    'mem20schoolz_create_learning_path'          => 'mem20schoolz',
    'mem20schoolz_doctor'                        => 'mem20schoolz',
    'mem20schoolz_evaluate_task'                 => 'mem20schoolz',
    'mem20schoolz_get_lesson'                    => 'mem20schoolz',
    'mem20schoolz_issue_credential'              => 'mem20schoolz',
    'mem20schoolz_list_courses'                  => 'mem20schoolz',
    'mem20schoolz_list_exams'                    => 'mem20schoolz',
    'mem20schoolz_log_session'                   => 'mem20schoolz',
    'mem20schoolz_mentor_match'                  => 'mem20schoolz',
    'mem20schoolz_mentorship_hours'              => 'mem20schoolz',
    'mem20schoolz_progression_plan'              => 'mem20schoolz',
    'mem20schoolz_register_mentor'               => 'mem20schoolz',
    'mem20schoolz_skill_level'                   => 'mem20schoolz',
    'mem20schoolz_status'                        => 'mem20schoolz',
    'mem20schoolz_take_exam'                     => 'mem20schoolz',
    'mem20schoolz_track_progress'                => 'mem20schoolz',
    'mem20schoolz_verify_credential'             => 'mem20schoolz',
    'memory_assess_confidence'                   => 'memory',
    'memory_audit_contamination'                 => 'memory',
    'memory_auto_consolidate'                    => 'memory',
    'memory_backfill_labels'                     => 'memory',
    'memory_cluster'                             => 'memory',
    'memory_consolidate'                         => 'memory',
    'memory_context_window'                      => 'memory',
    'memory_contradict'                          => 'memory',
    'memory_decay'                               => 'memory',
    'memory_deduplicate'                         => 'memory',
    'memory_detect_gaps'                         => 'memory',
    'memory_engine_guard'                        => 'memory_engine',
    'memory_engine_health'                       => 'memory_engine',
    'memory_engine_namespace'                    => 'memory_engine',
    'memory_engine_recall'                       => 'memory_engine',
    'memory_engine_subsystem'                    => 'memory_engine',
    'memory_engine_veto'                         => 'memory_engine',
    'memory_entity_extract'                      => 'memory',
    'memory_epistemic_veto'                      => 'memory',
    'memory_export'                              => 'memory',
    'memory_feedback'                            => 'memory',
    'memory_get_pinned_block'                    => 'memory',
    'memory_graph_traverse'                      => 'memory',
    'memory_import'                              => 'memory',
    'memory_index_health'                        => 'memory',
    'memory_ingest_audio'                        => 'memory',
    'memory_ingest_code'                         => 'memory',
    'memory_ingest_image'                        => 'memory',
    'memory_ingest_pdf'                          => 'memory',
    'memory_label_coverage'                      => 'memory',
    'memory_list_pinned_blocks'                  => 'memory',
    'memory_list_simulated'                      => 'memory',
    'memory_mood_tag'                            => 'memory',
    'memory_namespace_create'                    => 'memory',
    'memory_namespace_list'                      => 'memory',
    'memory_pin_block'                           => 'memory',
    'memory_probe'                               => 'memory',
    'memory_promote'                             => 'memory',
    'memory_quarantine_simulated'                => 'memory',
    'memory_reason'                              => 'memory',
    'memory_recall'                              => 'memory',
    'memory_recall_graph'                        => 'memory',
    'memory_recall_hybrid'                       => 'memory',
    'memory_recall_semantic'                     => 'memory',
    'memory_reinforce'                           => 'memory',
    'memory_related'                             => 'memory',
    'memory_scan_pii'                            => 'memory',
    'memory_self_audit'                          => 'memory',
    'memory_set_epistemic_status'                => 'memory',
    'memory_shared_recall'                       => 'memory',
    'memory_shared_store'                        => 'memory',
    'memory_simulate_store'                      => 'memory',
    'memory_stats'                               => 'memory',
    'memory_status'                              => 'memory',
    'memory_store'                               => 'memory',
    'memory_timeline'                            => 'memory',
    'memory_triggers'                            => 'memory',
    'memory_unpin_block'                         => 'memory',
    'milestoneriskpredictorz_status'             => 'mem20milestoneriskpredictorz',
    'mkt_ab_test'                                => 'marketing',
    'mkt_analytics'                              => 'marketing',
    'mkt_competitor_analysis'                    => 'marketing',
    'mkt_content_generate'                       => 'marketing',
    'mkt_email_campaign'                         => 'marketing',
    'mkt_hashtag_research'                       => 'marketing',
    'mkt_seo_analyze'                            => 'marketing',
    'mkt_social_analytics'                       => 'marketing',
    'mkt_social_post'                            => 'marketing',
    'offerassemblyfabricz_doctor'                => 'mem20offerassemblyfabricz',
    'offerassemblyfabricz_status'                => 'mem20offerassemblyfabricz',
    'offergenomeenginez_doctor'                  => 'mem20offergenomeenginez',
    'offergenomeenginez_status'                  => 'mem20offergenomeenginez',
    'opportunityradarz_doctor'                   => 'mem20opportunityradarz',
    'opportunityradarz_status'                   => 'mem20opportunityradarz',
    'ops_cli_audit'                              => 'ops',
    'ops_registry'                               => 'ops',
    'ops_wiring'                                 => 'ops',
    'outcomesimulationlabz_doctor'               => 'mem20outcomesimulationlabz',
    'outcomesimulationlabz_status'               => 'mem20outcomesimulationlabz',
    'personalautomationcanvasz_doctor'           => 'mem20personalautomationcanvasz',
    'personalautomationcanvasz_status'           => 'mem20personalautomationcanvasz',
    'personalcognitivesearchz_doctor'            => 'mem20personalcognitivesearchz',
    'personalcognitivesearchz_status'            => 'mem20personalcognitivesearchz',
    'personalmodelevolutionz_doctor'             => 'mem20personalmodelevolutionz',
    'personalmodelevolutionz_status'             => 'mem20personalmodelevolutionz',
    'personalworkflowtwinz_doctor'               => 'mem20personalworkflowtwinz',
    'personalworkflowtwinz_status'               => 'mem20personalworkflowtwinz',
    'pipelinez_doctor'                           => 'mem20pipelinez',
    'pipelinez_status'                           => 'mem20pipelinez',
    'planetarybatchfabricz_doctor'               => 'mem20planetarybatchfabricz',
    'planetarybatchfabricz_status'               => 'mem20planetarybatchfabricz',
    'playermotivationtwinz_doctor'               => 'mem20playermotivationtwinz',
    'playermotivationtwinz_status'               => 'mem20playermotivationtwinz',
    'predictiverecallenginez_doctor'             => 'mem20predictiverecallenginez',
    'predictiverecallenginez_status'             => 'mem20predictiverecallenginez',
    'prioritycollisionresolverz_status'          => 'mem20prioritycollisionresolverz',
    'procedural_add_skill'                       => 'procedural',
    'procedural_execute_skill'                   => 'procedural',
    'procedural_find_skills'                     => 'procedural',
    'procedural_get_skill'                       => 'procedural',
    'procedural_learn'                           => 'procedural',
    'procedural_list_skills'                     => 'procedural',
    'prod_goal_set'                              => 'productivity',
    'prod_habit_track'                           => 'productivity',
    'prod_meeting_notes'                         => 'productivity',
    'prod_note_create'                           => 'productivity',
    'prod_note_search'                           => 'productivity',
    'prod_project_create'                        => 'productivity',
    'prod_task_create'                           => 'productivity',
    'prod_task_list'                             => 'productivity',
    'prod_task_update'                           => 'productivity',
    'prod_time_track'                            => 'productivity',
    'productionplanningandtaskorchestrationpipelinez_doctor' => 'mem20productionplanningandtaskorchestrationpipelinez',
    'productionplanningandtaskorchestrationpipelinez_status' => 'mem20productionplanningandtaskorchestrationpipelinez',
    'productledgrowthsimulatorz_doctor'          => 'mem20productledgrowthsimulatorz',
    'productledgrowthsimulatorz_status'          => 'mem20productledgrowthsimulatorz',
    'protocolautodiscoveryenginez_doctor'        => 'mem20protocolautodiscoveryenginez',
    'protocolautodiscoveryenginez_status'        => 'mem20protocolautodiscoveryenginez',
    'react_reason'                               => 'thought_process',
    'realitytosoftwarecompilerz_doctor'          => 'mem20realitytosoftwarecompilerz',
    'realitytosoftwarecompilerz_status'          => 'mem20realitytosoftwarecompilerz',
    'realtimebusinesstwinz_doctor'               => 'mem20realtimebusinesstwinz',
    'realtimebusinesstwinz_status'               => 'mem20realtimebusinesstwinz',
    'realtimeeventautopilotz_doctor'             => 'mem20realtimeeventautopilotz',
    'realtimeeventautopilotz_status'             => 'mem20realtimeeventautopilotz',
    'realtimeteampresencez_doctor'               => 'mem20realtimeteampresencez',
    'realtimeteampresencez_status'               => 'mem20realtimeteampresencez',
    'realworldimpactrewardsz_doctor'             => 'mem20realworldimpactrewardsz',
    'realworldimpactrewardsz_status'             => 'mem20realworldimpactrewardsz',
    'reflexion'                                  => 'thought_process',
    'remoteexperimentlabz_doctor'                => 'mem20remoteexperimentlabz',
    'remoteexperimentlabz_status'                => 'mem20remoteexperimentlabz',
    'resourceexchangemarketz_doctor'             => 'mem20resourceexchangemarketz',
    'resourceexchangemarketz_status'             => 'mem20resourceexchangemarketz',
    'revenueleakhunterz_doctor'                  => 'mem20revenueleakhunterz',
    'revenueleakhunterz_status'                  => 'mem20revenueleakhunterz',
    'rewardforgez_doctor'                        => 'mem20rewardforgez',
    'rewardforgez_status'                        => 'mem20rewardforgez',
    'rigginganimationandmotionpipelinez_doctor'  => 'mem20rigginganimationandmotionpipelinez',
    'rigginganimationandmotionpipelinez_status'  => 'mem20rigginganimationandmotionpipelinez',
    'roadmap_create'                             => 'roadmap',
    'roadmap_get'                                => 'roadmap',
    'roadmap_list'                               => 'roadmap',
    'roadmap_update_phase'                       => 'roadmap',
    'roamingworkloadschedulerz_doctor'           => 'mem20roamingworkloadschedulerz',
    'roamingworkloadschedulerz_status'           => 'mem20roamingworkloadschedulerz',
    'runtimecompatibilityenginez_doctor'         => 'mem20runtimecompatibilityenginez',
    'runtimecompatibilityenginez_status'         => 'mem20runtimecompatibilityenginez',
    'runtimepromptoptimizerz_doctor'             => 'mem20runtimepromptoptimizerz',
    'runtimepromptoptimizerz_status'             => 'mem20runtimepromptoptimizerz',
    'scrape_api'                                 => 'webscraping',
    'scrape_dynamic'                             => 'webscraping',
    'scrape_forms'                               => 'webscraping',
    'scrape_page'                                => 'webscraping',
    'scrape_rss'                                 => 'webscraping',
    'scrape_sitemap'                             => 'webscraping',
    'scrape_structured'                          => 'webscraping',
    'scrape_submit_form'                         => 'webscraping',
    'search_academic'                            => 'search',
    'search_code'                                => 'search',
    'search_images'                              => 'search',
    'search_knowledge_base'                      => 'search',
    'search_local'                               => 'search',
    'search_news'                                => 'search',
    'search_web'                                 => 'search',
    'secretslessworkloadidentityz_doctor'        => 'mem20secretslessworkloadidentityz',
    'secretslessworkloadidentityz_status'        => 'mem20secretslessworkloadidentityz',
    'securecomputecapsulesz_doctor'              => 'mem20securecomputecapsulesz',
    'securecomputecapsulesz_status'              => 'mem20securecomputecapsulesz',
    'self_model_create'                          => 'memory',
    'self_model_get'                             => 'memory',
    'self_model_reflect'                         => 'memory',
    'selfhealingplansz_doctor'                   => 'mem20selfhealingplansz',
    'selfhealingplansz_status'                   => 'mem20selfhealingplansz',
    'selfoptimizingkernelz_doctor'               => 'mem20selfoptimizingkernelz',
    'selfoptimizingkernelz_status'               => 'mem20selfoptimizingkernelz',
    'selftuningresourcegovernorz_doctor'         => 'mem20selftuningresourcegovernorz',
    'selftuningresourcegovernorz_status'         => 'mem20selftuningresourcegovernorz',
    'selfz_doctor'                               => 'mem20selfz',
    'selfz_status'                               => 'mem20selfz',
    'sensorymemoryingestz_doctor'                => 'mem20sensorymemoryingestz',
    'sensorymemoryingestz_status'                => 'mem20sensorymemoryingestz',
    'servicebundlingenginez_doctor'              => 'mem20servicebundlingenginez',
    'servicebundlingenginez_status'              => 'mem20servicebundlingenginez',
    'simz_doctor'                                => 'mem20simz',
    'simz_status'                                => 'mem20simz',
    'skillbasedprogressionbrainz_doctor'         => 'mem20skillbasedprogressionbrainz',
    'skillbasedprogressionbrainz_status'         => 'mem20skillbasedprogressionbrainz',
    'skillmemorytransferz_doctor'                => 'mem20skillmemorytransferz',
    'skillmemorytransferz_status'                => 'mem20skillmemorytransferz',
    'spatialcommanduniversez_doctor'             => 'mem20spatialcommanduniversez',
    'spatialcommanduniversez_status'             => 'mem20spatialcommanduniversez',
    'specialistmodelforgez_doctor'               => 'mem20specialistmodelforgez',
    'specialistmodelforgez_status'               => 'mem20specialistmodelforgez',
    'speculativeworkflowenginez_doctor'          => 'mem20speculativeworkflowenginez',
    'speculativeworkflowenginez_status'          => 'mem20speculativeworkflowenginez',
    'stream_publish'                             => 'eventstream',
    'stream_recall'                              => 'eventstream',
    'stream_report'                              => 'eventstream',
    'stream_search'                              => 'eventstream',
    'stream_verify'                              => 'eventstream',
    'studioz_doctor'                             => 'mem20studioz',
    'studioz_status'                             => 'mem20studioz',
    'styleguideagentz_doctor'                    => 'mem20styleguideagentz',
    'styleguideagentz_status'                    => 'mem20styleguideagentz',
    'syntheticevaluatorarenaz_doctor'            => 'mem20syntheticevaluatorarenaz',
    'syntheticevaluatorarenaz_status'            => 'mem20syntheticevaluatorarenaz',
    'temporal_doctor'                            => 'temporal',
    'temporal_get'                               => 'temporal',
    'temporal_ingest'                            => 'temporal',
    'temporal_put'                               => 'temporal',
    'temporal_slices'                            => 'temporal',
    'theory_of_mind_perspective'                 => 'cognitive',
    'theory_of_mind_simulate'                    => 'cognitive',
    'toolchest_inventory'                        => 'toolchest',
    'toolchest_wiring'                           => 'toolchest',
    'tot_diagnose'                               => 'thought_process',
    'tot_modeling'                               => 'thought_process',
    'tot_reason'                                 => 'thought_process',
    'twinz_doctor'                               => 'mem20twinz',
    'twinz_status'                               => 'mem20twinz',
    'uniteconomicsautopilotz_doctor'             => 'mem20uniteconomicsautopilotz',
    'uniteconomicsautopilotz_status'             => 'mem20uniteconomicsautopilotz',
    'unity_build_project'                        => 'unity',
    'unity_create_script'                        => 'unity',
    'unity_generate_asmdef'                      => 'unity',
    'unity_run_test'                             => 'unity',
    'unity_validate_project'                     => 'unity',
    'universalhealthnervoussystemz_doctor'       => 'mem20universalhealthnervoussystemz',
    'universalhealthnervoussystemz_status'       => 'mem20universalhealthnervoussystemz',
    'universalintegrationcompilerz_doctor'       => 'mem20universalintegrationcompilerz',
    'universalintegrationcompilerz_status'       => 'mem20universalintegrationcompilerz',
    'vcs_asset_release_audit'                    => 'rm239',
    'vcs_git_blame'                              => 'versioncontrol',
    'vcs_git_branch'                             => 'versioncontrol',
    'vcs_git_commit'                             => 'versioncontrol',
    'vcs_git_diff'                               => 'versioncontrol',
    'vcs_git_log'                                => 'versioncontrol',
    'vcs_git_remote'                             => 'versioncontrol',
    'vcs_git_stash'                              => 'versioncontrol',
    'vcs_git_status'                             => 'versioncontrol',
    'vcs_git_tag'                                => 'versioncontrol',
    'vcs_github_issue'                           => 'versioncontrol',
    'vcs_github_pr'                              => 'versioncontrol',
    'verify_drift'                               => 'verify',
    'verify_lint'                                => 'verify',
    'verify_tests'                               => 'verify',
    'verify_wiring'                              => 'verify',
    'visualagentblackboardz_doctor'              => 'mem20visualagentblackboardz',
    'visualagentblackboardz_status'              => 'mem20visualagentblackboardz',
    'visualdataflowcomposerz_doctor'             => 'mem20visualdataflowcomposerz',
    'visualdataflowcomposerz_status'             => 'mem20visualdataflowcomposerz',
    'webhook_deliver'                            => 'webhook',
    'webhook_doctor'                             => 'webhook',
    'webhook_replay'                             => 'webhook',
    'webhook_route_capabilities'                 => 'webhook',
    'webhook_verify'                             => 'webhook',
    'world_model_add_rule'                       => 'world',
    'world_model_add_variable'                   => 'world',
    'world_model_get_state'                      => 'world',
    'world_model_predict'                        => 'world',
    'world_model_record_prediction'              => 'world',
    'world_model_reset'                          => 'world',
    'world_model_resolve_prediction'             => 'world',
    'world_model_simulate'                       => 'world',
    'zerodowntimemigrationbrainz_status'         => 'mem20zerodowntimemigrationbrainz',
    'zerotouchnodeswarmz_doctor'                 => 'mem20zerotouchnodeswarmz',
    'zerotouchnodeswarmz_status'                 => 'mem20zerotouchnodeswarmz',

);

# Domain => the tools it owns, built from %TOOL_DOMAIN so the two can never
# disagree.
our %DOMAIN_TOOLS;
{
    my %by_domain;
    push @{ $by_domain{ $TOOL_DOMAIN{$_} } }, $_ for sort keys %TOOL_DOMAIN;
    %DOMAIN_TOOLS = %by_domain;
}

# The domain names, sorted.
our @DOMAIN_NAMES = sort keys %DOMAIN_TOOLS;

# True when the server advertises this tool.
sub has_tool {
    my ( $class, $name ) = @_;
    return 0 unless defined $name;
    return exists $TOOL_DOMAIN{$name} ? 1 : 0;
}

# The domain that owns a tool, or undef.
sub domain_of {
    my ( $class, $name ) = @_;
    return undef unless defined $name;
    return $TOOL_DOMAIN{$name};
}

# The tools owned by a domain, as a list. Empty when the domain is unknown.
sub tools_in {
    my ( $class, $domain ) = @_;
    return () unless defined $domain;
    return @{ $DOMAIN_TOOLS{$domain} || [] };
}

# Compare a live tool-name list against this manifest.
#
# Returns a hashref with the counts, the names the server advertises but this
# SDK does not know (extra), and the names this SDK expects but the server did
# not advertise (missing). Both lists are sorted, so a failure message is
# stable across runs.
sub diff {
    my ( $class, $live_names ) = @_;

    my %live  = map { $_ => 1 } @{ $live_names || [] };
    my %known = map { $_ => 1 } @TOOL_NAMES;

    my @missing = sort grep { !$live{$_} } @TOOL_NAMES;
    my @extra   = sort grep { !$known{$_} } keys %live;

    return {
        ok             => ( @missing || @extra ) ? 0 : 1,
        tools          => scalar keys %live,
        expected_tools => $TOOL_COUNT,
        domains        => $DOMAIN_COUNT,
        missing        => \@missing,
        extra          => \@extra,
    };
}

1;
__END__

=head1 NAME

Mem20::Surface - the mem20 tool surface this SDK was generated against

=head1 DESCRIPTION

B<Generated file.> Do not edit by hand; run C<perl xt/gen-surface.pl>.

Holds the full tool-name list (527 names) and the tool-to-domain map
(135 domains) that C<Mem20::Client/verify_surface> compares a live
C<tools/list> against. A count alone cannot say I<which> tool moved; this
module can.

The data comes from C<docs/surface.json> and C<web/src/data/tools.json> in the
mem20 repository, which C<scripts/surface_manifest.py> generates from a live
C<tools/list> round trip and cross-checks against an AST scan of the tool
modules. The generator refuses to emit unless the two agree.

=head1 CLASS METHODS

=over 4

=item C<< Mem20::Surface->has_tool($name) >> - is this tool advertised?

=item C<< Mem20::Surface->domain_of($name) >> - the owning domain, or undef.

=item C<< Mem20::Surface->tools_in($domain) >> - the tools a domain owns.

=item C<< Mem20::Surface->diff(\@live_names) >> - compare a live list against
this manifest. Returns C<ok>, C<tools>, C<expected_tools>, C<domains>,
C<missing> and C<extra>.

=back

=head1 VARIABLES

C<$TOOL_COUNT>, C<$DOMAIN_COUNT>, C<@TOOL_NAMES>, C<%TOOL_DOMAIN>,
C<%DOMAIN_TOOLS>, C<@DOMAIN_NAMES>.

=cut
