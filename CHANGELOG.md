# Changelog


## release/v0.5.0 (2024-09-15)

### Add

* Add: automatic_reference to mongoengine. [Julius Koenig]

* Add: end_step attr for FinalizeCommand. [Julius Koenig]

### Changes

* Drop ActionLog.Thread - allow inline payload params. [Julius Koenig]

* ActionLog.Thread - allow inline payload params. [Julius Koenig]

### Fix

* ActionLogger finalize msg. [Julius Koenig]

### Other

* Merge remote-tracking branch 'origin/main' [Julius Koenig]

* Wip. [Julius Koenig]


## release/v0.4.7 (2024-09-05)

### Add

* Add: post_init.py. [Julius Koenig]

### Fix

* Wiederverwendbar/starlette_admin/mongoengine/generic_embedded_document_field/field.py - Field name '__doc_name__' not found. [Julius Koenig]

* Add nest_asyncio to full install mode. [Julius Koenig]


## release/v0.4.6 (2024-08-14)

### Add

* Add: form for ActionLogger. [Julius Koenig]

### Fix

* ActionLogger outside of debug mode, ugly hack to make asyncio.run. [Julius Koenig]

* On multiple forms "onclick" event is triggered multiple times. [Julius Koenig]


## release/v0.4.5 (2024-08-13)

### Add

* Add: YesNoCommand for ActionLog. [Julius Koenig]


## release/v0.4.4 (2024-08-13)

### Add

* Add: push-tags pdm command. [Julius Koenig]

### Fix

* Form data result. [Julius Koenig]


## release/v0.4.3 (2024-08-13)

### Add

* Add: form request for ActionLog. [Julius Koenig]


## release/v0.4.2 (2024-08-12)

### Add

* Add: ActionLogThread. [Julius Koenig]


## release/v0.4.1 (2024-08-09)

### Changes

* Version to v0.4.1. [Julius Koenig]

### Fix

* Starlette_admin.mongoengine.auth.views.users acls field. [Julius Koenig]

* Action_log increase_steps if steps None. [Julius Koenig]

* Settings admin_session_secret_key, admin_session_absolute_max_age  in wrong class. [Julius Koenig]


## release/v0.4.0 (2024-08-09)

### Add

* Add: IncreaseStepsCommand. [Julius Koenig]

* Add: BooleanAlsoField to starlette_admin mongoengine sub subpackage. [Julius Koenig]

* Add: BooleanAlsoField, WithInstanceField to mongoengine subpackage. [Julius Koenig]

* Add: DropDownIconView sub subpackage for starlette_admin subpackage. [Julius Koenig]

* Add: AuthView. [Julius Koenig]

* Add: settings admin_superuser_username, admin_superuser_auto_create, admin_user_allows_empty_password_login. [Julius Koenig]

* Add: thumbnail option for user avatar. [Julius Koenig]

### Changes

* Format pyproject.toml. [Julius Koenig]

* Update .gitchangelog.rc tag filter. [Julius Koenig]

* Space build recept build. [Julius Koenig]

* Reorg dependencies. [Julius Koenig]

* .gitchangelog.rc - fix ignore. [Julius Koenig]

* .gitchangelog.rc - fix ignore. [Julius Koenig]

* Space build recept build. [Julius Koenig]

### Fix

* MultiPathAdmin wrong order static_files_packages, template_packages in starlette_admin subpackage. [Julius Koenig]

* User password set. [Julius Koenig]

* None set avatar_url for provider. [Julius Koenig]

* None set custom_logo_url for provider. [Julius Koenig]

* Session deletion on user delete. [Julius Koenig]

### Other

* Update test files. [Julius Koenig]

* Merge remote-tracking branch 'origin/wip/v0.4.0' into wip/v0.4.0. [Julius Koenig]

* V0.4.0: - wip. [Julius Koenig]

* V0.4.0: - wip. [Julius Koenig]


## release/v0.3.3 (2024-08-01)

### Changes

* Update dependecies add: pkg: add gitchangelog as dependency add: doc: add changelog. [Julius Koenig]


## release/v0.3.2 (2024-08-01)

### Other

* V0.3.2 - functions   - remove imports. [Julius Koenig]


## release/v0.3.1 (2024-07-30)

### Other

* V0.3.1 - starlette_admin   - fix generic_embedded.js -> shows multiple fields on similar names. [Julius Koenig]


## release/v0.3.0 (2024-07-29)

### Other

* V0.3.0 - update dependencies - starlette_admin   - better error handling for ActionLogger   - add halt_on_error for ActionLogger and ActionSubLoggerContext. [Julius Koenig]

* V0.3.0 - reorg package structure - splitt Singleton into ModelSingleton(pydantic) and Singleton(generic) [Julius Koenig]

* V0.2.31   - starlette_admin     - add StepCommand, NextStepCommand, FinalizeCommand, ExitCommand class to control action log from everywhere     - add on_success_msg and on_error_msg to ActionSubLogger.finalize()     - set action log to fixed size instead of dynamic resizing     - remove unused code in actions.js     - fix SubLoggerContext(LoggingContext)     - fix using log level from parent always if parent is set in ActionLogger or ActionSubLoggerContext     - add parameter to wrap LoggingContext   - logger     - add thread functionality to LoggingContext     - add functionality for using LoggingContext without context variable     - improve logger_context example     - fix various errors (dict resized by iteration)     - allow manually restoring of wrapped Loggers in LoggingContext     - improve LoggingContext.need_update     - add get_from_stack class method to LoggingContext     - add use_context_logger_level, use_context_logger_level_on_not_set, ignore_loggers_equal and ignore_loggers_like attributes to LoggingContext(also functionality) [Julius Koenig]


## release/v0.2.31 (2024-07-29)

### Other

* V0.2.31   - starlette_admin     - use LoggingContext in ActionLogger. [Julius Koenig]

* V0.2.30   - starlette_admin     - use LoggingContext in ActionLogger. [Julius Koenig]


## release/v0.2.30 (2024-07-29)

### Other

* V0.2.30   - logger     - add LoggingContext     - add examples for LoggingContext. [Julius Koenig]

* V0.2.30   - starlette_admin:     - fix log_leve inheritance for ActionLogger and SubActionLogger   - logger     - add reconfigure contextmanager for SubLogger     - add get_logger class method for SubLogger. [Julius Koenig]


## release/v0.2.29 (2024-07-25)

### Other

* V0.2.29   - starlette_admin:     - fix finalize in ActionLogger     - fix exception tracback in ActionLogger. [Julius Koenig]


## release/v0.2.28 (2024-07-25)

### Other

* V0.2.28   - logger:     - fix singleton logger. [Julius Koenig]

* V0.2.28   - logger:     - fix singleton logger. [Julius Koenig]


## release/v0.2.27 (2024-07-25)

### Other

* V0.2.27   - starlette-admin:     - add FormMaxFieldsAdmin. [Julius Koenig]


## release/v0.2.26 (2024-07-25)

### Other

* V0.2.26   - starlette-admin:     - add action_log     - add multipath admin     - reorganize package structure     - add/modify examples. [Julius Koenig]

* V0.2.26   - wip - add action_log for starlette-admin. [Julius Koenig]

* V0.2.26   - wip - add action_log for starlette-admin. [Julius Koenig]

* V0.2.26   - wip - add action_log for starlette-admin. [Julius Koenig]

* V0.2.26   - wip - add action_log for starlette-admin. [Julius Koenig]

* V0.2.26   - add action_log for starlette-admin. [Julius Koenig]


## release/v0.2.25 (2024-07-17)

### Other

* V0.2.25   - fix validation error on emb list field. [Julius Koenig]


## release/v0.2.24 (2024-07-17)

### Other

* V0.2.24   - fix validation error on emb list field. [Julius Koenig]


## release/v0.2.23 (2024-07-15)

### Other

* V0.2.23   - reorg internal package structure starlette_admin   - add PropertyModelView. [Julius Koenig]

* V0.2.23   - reorg internal package structure starlette_admin. [Julius Koenig]

* V0.2.23   - add render_function_key = "text" option for list view. [Julius Koenig]

* V0.2.23   - remove print_console in eval_value and eval_file. [Julius Koenig]

* V0.2.23   - fix field required validation. [Julius Koenig]

* V0.2.23   - fix initialization of generic emb selects. [Julius Koenig]

* V0.2.23   - fix static mount overwrite. [Julius Koenig]


## release/v0.2.22 (2024-07-12)

### Other

* V0.2.21   - remove class FixedCollectionField and converter for better fix via forms.js   - add ListField Support for GenericEmbeddedDocumentField. [Julius Koenig]

* V0.2.21   - add class ModelView for fixing ObjectId to str converting   - add ipv4 field converter. [Julius Koenig]


## release/v0.2.20 (2024-07-11)

### Other

* V0.2.20 - update dependencies - add example file_config.py - add example indexable_model.py - add example logger.py - add example singletons.py - add starlette_admin subpackage   - add class Admin   - add class GenericEmbeddedDocumentField and converter   - add class FixedCollectionField and converter   - add example generic_embedded_document_field.py. [Julius Koenig]


## release/v0.2.19 (2024-07-10)

### Other

* V0.2.19 - add animal_name_generator.py - add hash_password.py - add hashed_password_document.py - add hashed_password_model.py - add verify_password.py. [Julius Koenig]

* V0.2.19 - add task manager. [Julius Koenig]

* V0.2.19 - merge from kdsm-poller. [Julius Koenig]

* V0.1.0: - wip. [Julius Koenig]

* V0.1.0: - wip. [Julius Koenig]

* V0.1.0: - wip. [Julius Koenig]

* V0.1.0: - wip. [Julius Koenig]

* V0.1.0: - wip. [Julius Koenig]


## release/v0.2.18 (2024-06-26)

### Other

* V0.2.18 - add IPv4NetworkField. [Julius Koenig]


## release/v0.2.17 (2024-06-21)

### Other

* V0.2.17 - add typer_resolve_defaults. [Julius Koenig]

* V0.2.17 - wip. [Julius König]


## release/v0.2.16 (2024-06-10)

### Other

* V0.2.16 - add compatibility for python3.9. [Julius König]


## release/v0.2.15 (2024-06-10)

### Other

* V0.2.15 - add compatibility for python3.9. [Julius König]

* V0.2.15 - add compatibility for python3.9. [Julius König]


## release/v0.2.14 (2024-06-10)

### Other

* V0.2.14 - chang python requirements. [Julius König]


## release/v0.2.13 (2024-06-05)

### Other

* V0.2.13 - fix find_class_method bases is not iterable. [Julius König]


## release/v0.2.12 (2024-06-03)

### Other

* V0.2.12 - fix before_after_wrap.py   - add include_inherited flag. [Julius König]


## release/v0.2.11 (2024-06-03)

### Other

* V0.2.11 - add fix example. [Julius König]

* V0.2.11 - bump version. [Julius König]


## release/v0.2.10 (2024-05-31)

### Other

* V0.2.10 - add before_after_wrap. [Julius König]

* V0.2.9 - add validate_log_level for LoggerSettings. [Julius König]


## release/v0.2.9 (2024-05-30)

### Other

* V0.2.9 - fix mongoengine backup. [Julius König]


## release/v0.2.8 (2024-05-30)

### Other

* V0.2.8 - add mongoengine backup. [Julius König]


## release/v0.2.7 (2024-05-29)

### Other

* V0.2.7 - add mongoengine - add ipv4_address_field.py - add property_document.py. [Julius König]

* V0.2.7 - remove print. [Julius König]


## release/v0.2.6 (2024-05-29)

### Other

* V0.2.6 - add eval_value.py, eval_file.py - add wait_ping.py. [Julius König]

* V0.2.6 - add admin.py. [Julius König]


## release/v0.2.5 (2024-05-29)

### Other

* V0.2.5 - add logging for singleton.py. [Julius König]

* V0.2.5 - add logging for singleton.py. [Julius König]

* V0.2.5 - add atexit hook for singleton.py. [Julius König]


## release/v0.2.4 (2024-05-24)

### Other

* V0.2.4 - move models to pydantic. [Julius König]


## release/v0.2.3 (2024-05-23)

### Other

* V0.2.3 - implement SubLogger. [Julius König]


## release/v0.2.2 (2024-05-23)

### Other

* V0.2.2 - implement ordering of singletons and deleting. [Julius König]


## release/v0.2.1 (2024-05-23)

### Other

* V0.2.1 - add Logger, LoggerSettings, LoggerSingleton to __init__.py - add models. [Julius König]

* V0.2.1 - add Logger, LoggerSettings, LoggerSingleton to __init__.py. [Julius König]

* V0.2.1 - add Logger, LoggerSettings, LoggerSingleton to __init__.py. [Julius König]


## release/v0.2.0 (2024-05-23)

### Other

* V0.2.0 - add singleton.py - add logger. [Julius König]

* V0.2.0 - add singleton.py - add logger. [Julius König]

* V0.2.0 - add singleton.py - add logger. [Julius König]

* V0.2.0 - add singleton.py - add logger. [Julius König]

* Initial commit. [Julius König]

* Initial commit. [Julius König]


