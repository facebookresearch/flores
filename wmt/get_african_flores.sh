#!/bin/bash

mkdir -p african_flores
mkdir -p african_flores/dev
mkdir -p african_flores/devtest

# download flores101 and flores_wmt22_supplement
wget https://dl.fbaipublicfiles.com/flores101/dataset/flores101_dataset.tar.gz
wget https://dl.fbaipublicfiles.com/flores101/dataset/flores_wmt22_supplement.tar.gz

# unzip downloaded files.
tar -xf flores101_dataset.tar.gz
tar -xf flores_wmt22_supplement.tar.gz


# move flores_wmt22_supplement dev and devtest to african_flores
for lang in kin ssw tsn tso
do
	for split in dev devtest
	do
		cp -r flores_wmt22_supplement/$split/$lang.$split african_flores/$split/
	done
done

# move flores101 dev and devtest to african_flores
for lang in afr amh eng fra ful hau ibo kam lin lug luo nso nya orm sna som swh umb wol xho yor zul
do
	for split in dev devtest
	do
		cp -r flores101_dataset/$split/$lang.$split african_flores/$split/
	done
done

# delete archive and unused folders
rm -r flores*

