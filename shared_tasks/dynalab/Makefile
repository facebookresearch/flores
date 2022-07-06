MODEL_NAME=m2m-124-175m

# test: simple_test_$(MODEL_NAME) docker_test_$(MODEL_NAME)
test: docker_test_$(MODEL_NAME)


# Download and extract baseline model
dl_$(MODEL_NAME): $(MODEL_NAME).pt


$(MODEL_NAME).pt: flores101_mm100_175M.tar.gz
	tar -xzf $<
	mv flores101_mm100_175M/model.pt $@
	touch $@
	mv flores101_mm100_175M/* .
	rm -r flores101_mm100_175M/


flores101_mm100_175M.tar.gz:
	wget https://dl.fbaipublicfiles.com/flores101/pretrained_models/flores101_mm100_175M.tar.gz


# Setup dynalab
dyna_init_$(MODEL_NAME): .dynalab/$(MODEL_NAME)


.dynalab/$(MODEL_NAME):
	dynalab-cli init \
		--name $(MODEL_NAME) \
		--task flores_small1 \
		--handler handler.py \
		--model-checkpoint $(MODEL_NAME).pt \
		--install-requirements \
		--model-files sentencepiece.bpe.model,model_generation.json,dict.txt


# Run dynalab tests
simple_test_$(MODEL_NAME): $(MODEL_NAME).pt .dynalab/$(MODEL_NAME) handler.py
	# python -m pdb `which dynalab-cli` test --local -n $(MODEL_NAME)
	dynalab-cli test --local -n $(MODEL_NAME)


docker_test_$(MODEL_NAME): $(MODEL_NAME).pt .dynalab/$(MODEL_NAME) handler.py
	dynalab-cli test -n $(MODEL_NAME)

# .dynalab/$(MODEL_NAME)/tmp/$(MODEL_NAME).mar: .dynalab/$(MODEL_NAME) handler.py $(MODEL_NAME).pt


