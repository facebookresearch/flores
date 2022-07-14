# Toxicity-200

** Warning: The files included in this contain toxic language. **

This repository contains files that include frequent words and phrases generally considered toxic because they represent:
* Frequently used profanities
* Frequently used insults and hate speech terms, or language used to bully, denigrate, or demean
* Pornographic terms
* Terms for body parts associated with sexual activity

--------------------------------------------------------------------------------

## Download

Toxicity-200 can be downloaded [here](https://tinyurl.com/NLLB200TWL) which you can download with the following command:

```bash
wget --trust-server-names https://tinyurl.com/NLLB200TWL
```

## Purpose, Ethical Considerations, and Use of the Lists
The primary purpose of such lists is to help with translation model safety by monitoring for hallucinated toxicity. By *hallucinated toxicity*, we mean the presence of toxic items in the translated text when no such toxic items can be found in the source text.

The lists were collected via human translation. Any such translation effort inevitably poses risks of bias. The likelihood of getting access to professionals with diverse backgrounds and worldviews is not equal across all supported languages. In addition to the work that has already been done to mitigate biases, which can also introduce its own potential biases, the ultimate mitigation strategy can be to provide the community with free access to the lists, and to welcome feedback and contributions from the community in all supported languages.

The files are in zip format, and unzipping is password protected. To unzip the files after downloading, you may use the following command line:
`unzip --password tL4nLLb [BCP47_code]_twl.zip`
The unzipping of the files implies that you consent to viewing their contents.

Language codes for all languages can be found in the below table (see **Project Status**). The BCP 47 language codes include an ISO 639-3 base tag to identify the language and ISO 15924 supplemental tag to identify the script (e.g., taq_Tfng for Tamasheq in Tifinagh script). The codes mirror those used for the release of the FLORES-200 data sets. However, in cases where FLORES-200 targets a specific lect, the corresponding lists may not be as restrictive in that they may include items from closely related lects.

## Languages in Toxicity-200
The following toxicity lists are currently available in these languages:

BCP 47 Code | Language
----------- | ----------------------------------
ace_Arab    | Acehnese (Arabic script)
ace_Latn    | Acehnese (Latin script)
acm_Arab    | Mesopotamian Arabic
acq_Arab    | Ta’izzi-Adeni Arabic
aeb_Arab    | Tunisian Arabic
afr_Latn    | Afrikaans
ajp_Arab    | South Levantine Arabic
aka_Latn    | Akan
als_Latn    | Tosk Albanian
amh_Ethi    | Amharic
apc_Arab    | North Levantine Arabic
arb_Arab    | Modern Standard Arabic
arb_Latn    | Modern Standard Arabic (Romanized)
ars_Arab    | Najdi Arabic
ary_Arab    | Moroccan Arabic
arz_Arab    | Egyptian Arabic
asm_Beng    | Assamese
ast_Latn    | Asturian
awa_Deva    | Awadhi
ayr_Latn    | Central Aymara
azb_Arab    | South Azerbaijani
azj_Latn    | North Azerbaijani
bak_Cyrl    | Bashkir
bam_Latn    | Bambara
ban_Latn    | Balinese
bel_Cyrl    | Belarusian
bem_Latn    | Bemba
ben_Beng    | Bengali
bho_Deva    | Bhojpuri
bjn_Arab    | Banjar (Arabic script)
bjn_Latn    | Banjar (Latin script)
bod_Tibt    | Standard Tibetan
bos_Latn    | Bosnian
bug_Latn    | Buginese
bul_Cyrl    | Bulgarian
cat_Latn    | Catalan
ceb_Latn    | Cebuano
ces_Latn    | Czech
cjk_Latn    | Chokwe
ckb_Arab    | Central Kurdish
crh_Latn    | Crimean Tatar
cym_Latn    | Welsh
dan_Latn    | Danish
deu_Latn    | German
dik_Latn    | Southwestern Dinka
dyu_Latn    | Dyula
dzo_Tibt    | Dzongkha
ell_Grek    | Greek
eng_Latn    | English
epo_Latn    | Esperanto
est_Latn    | Estonian
eus_Latn    | Basque
ewe_Latn    | Ewe
fao_Latn    | Faroese
fij_Latn    | Fijian
fin_Latn    | Finnish
fon_Latn    | Fon
fra_Latn    | French
fur_Latn    | Friulian
fuv_Latn    | Nigerian Fulfulde
gaz_Latn    | West Central Oromo
gla_Latn    | Scottish Gaelic
gle_Latn    | Irish
glg_Latn    | Galician
grn_Latn    | Guarani
guj_Gujr    | Gujarati
hat_Latn    | Haitian Creole
hau_Latn    | Hausa
heb_Hebr    | Hebrew
hin_Deva    | Hindi
hne_Deva    | Chhattisgarhi
hrv_Latn    | Croatian
hun_Latn    | Hungarian
hye_Armn    | Armenian
ibo_Latn    | Igbo
ilo_Latn    | Ilocano
ind_Latn    | Indonesian
isl_Latn    | Icelandic
ita_Latn    | Italian
jav_Latn    | Javanese
jpn_Jpan    | Japanese
kab_Latn    | Kabyle
kac_Latn    | Jingpho
kam_Latn    | Kamba
kan_Knda    | Kannada
kas_Arab    | Kashmiri (Arabic script)
kas_Deva    | Kashmiri (Devanagari script)
kat_Geor    | Georgian
kaz_Cyrl    | Kazakh
kbp_Latn    | Kabiyè
kea_Latn    | Kabuverdianu
khk_Cyrl    | Halh Mongolian
khm_Khmr    | Khmer
kik_Latn    | Kikuyu
kin_Latn    | Kinyarwanda
kir_Cyrl    | Kyrgyz
kmb_Latn    | Kimbundu
kmr_Latn    | Northern Kurdish
knc_Arab    | Central Kanuri (Arabic script)
knc_Latn    | Central Kanuri (Latin script)
kon_Latn    | Kikongo
kor_Hang    | Korean
lao_Laoo    | Lao
lij_Latn    | Ligurian
lim_Latn    | Limburgish
lin_Latn    | Lingala
lit_Latn    | Lithuanian
lmo_Latn    | Lombard
ltg_Latn    | Latgalian
ltz_Latn    | Luxembourgish
lua_Latn    | Luba-Kasai
lug_Latn    | Ganda
luo_Latn    | Luo
lus_Latn    | Mizo
lvs_Latn    | Standard Latvian
mag_Deva    | Magahi
mai_Deva    | Maithili
mal_Mlym    | Malayalam
mar_Deva    | Marathi
min_Arab    | Minangkabau (Arabic script)
min_Latn    | Minangkabau (Latin script)
mkd_Cyrl    | Macedonian
mlt_Latn    | Maltese
mni_Beng    | Meitei (Bengali script)
mos_Latn    | Mossi
mri_Latn    | Maori
mya_Mymr    | Burmese
nld_Latn    | Dutch
nno_Latn    | Norwegian Nynorsk
nob_Latn    | Norwegian Bokmål
npi_Deva    | Nepali
nso_Latn    | Northern Sotho
nus_Latn    | Nuer
nya_Latn    | Nyanja
oci_Latn    | Occitan
ory_Orya    | Odia
pag_Latn    | Pangasinan
pan_Guru    | Eastern Panjabi
pap_Latn    | Papiamento
pbt_Arab    | Southern Pashto
pes_Arab    | Western Persian
plt_Latn    | Plateau Malagasy
pol_Latn    | Polish
por_Latn    | Portuguese
prs_Arab    | Dari
quy_Latn    | Ayacucho Quechua
ron_Latn    | Romanian
run_Latn    | Rundi
rus_Cyrl    | Russian
sag_Latn    | Sango
san_Deva    | Sanskrit
sat_Olck    | Santali
scn_Latn    | Sicilian
shn_Mymr    | Shan
sin_Sinh    | Sinhala
slk_Latn    | Slovak
slv_Latn    | Slovenian
smo_Latn    | Samoan
sna_Latn    | Shona
snd_Arab    | Sindhi
som_Latn    | Somali
sot_Latn    | Southern Sotho
spa_Latn    | Spanish
srd_Latn    | Sardinian
srp_Cyrl    | Serbian
ssw_Latn    | Swati
sun_Latn    | Sundanese
swe_Latn    | Swedish
swh_Latn    | Swahili
szl_Latn    | Silesian
tam_Taml    | Tamil
taq_Latn    | Tamasheq (Latin script)
taq_Tfng    | Tamasheq (Tifinagh script)
tat_Cyrl    | Tatar
tel_Telu    | Telugu
tgk_Cyrl    | Tajik
tgl_Latn    | Tagalog
tha_Thai    | Thai
tir_Ethi    | Tigrinya
tpi_Latn    | Tok Pisin
tsn_Latn    | Tswana
tso_Latn    | Tsonga
tuk_Latn    | Turkmen
tum_Latn    | Tumbuka
tur_Latn    | Turkish
twi_Latn    | Twi
tzm_Tfng    | Central Atlas Tamazight
uig_Arab    | Uyghur
ukr_Cyrl    | Ukrainian
umb_Latn    | Umbundu
urd_Arab    | Urdu
uzn_Latn    | Northern Uzbek
vec_Latn    | Venetian
vie_Latn    | Vietnamese
war_Latn    | Waray
wol_Latn    | Wolof
xho_Latn    | Xhosa
ydd_Hebr    | Eastern Yiddish
yor_Latn    | Yoruba
yue_Hant    | Yue Chinese
zho_Hans    | Chinese (Simplified)
zho_Hant    | Chinese (Traditional)
zsm_Latn    | Standard Malay
zul_Latn    | Zulu

