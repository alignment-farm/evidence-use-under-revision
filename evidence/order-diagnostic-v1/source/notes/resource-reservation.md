Development reservation: local Apple Silicon 64GiB host, one MLX process for this
study, no heavy Python model processes observed before launch. Own advisory lock
/tmp/evidence-use-under-revision.lock plus sibling-process check between operations.
This is passive local coordination, not an inter-study atomic scheduler. All local
weight files are read-only inputs. Dedicated remote serving is not needed because
native gradient access exists locally. Model and MLX caps recorded per invocation.
