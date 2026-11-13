# Backup quiz (plain Qwen3-0.6B, one call per question) on the 40 eval passages

Judge: Sonnet against docs/QUESTION_RUBRIC.md, blind to variant and to kept/rejected.

| Variant | Passages with >= 3 questions | Questions shown | Key correct | Score >= 4 (good) | Score <= 2 (bad) | Pi time per quiz (est. 60/20 tok/s), median / max |
|---|---|---|---|---|---|---|
| ft | 26/40 | 115 | 94/115 | 0/115 | 113/115 | 53.9 s / 73.0 s |
- **ft: sensible 35/115** (key right, all options on topic and grammatical, answer not obvious; the lower, practical bar)

## Did the self-check help? (rejected-by-self-check questions vs shown ones, same judge)

- ft: questions the self-check threw out had a correct key 17/40 times, score >= 4 in 0/40

## Why questions were rejected

- ft: answer leaked in question x13
- ft: could not parse x4
- ft: repeated option x55
- ft: self-check failed x40
- ft: too long x2

## Every shown question with its grade

**bio_digestion [ft] score 1 key OK not sensible H1 H3 H4 H5 H6**: What is the process of breaking down food into simple substances that the body can absorb called?  
  - absorption  
  ✅ digestion  
  - metabolism  
  _Only three options; definition recall; absorption distractor arguably fits; no explanation._

**bio_digestion [ft] score 2 key OK not sensible H1 H4 H6**: What organ is the food passed into after being partially digested in the stomach?  
  ✅ small intestine  
  - small liver  
  - large intestine  
  - large liver  
  _Recall; 'small liver' and 'large liver' are nonexistent, silly distractors._

**bio_digestion [ft] score 1 key OK not sensible H1 H4 H6**: What organ is shorter but wider, where water and some salts are absorbed?  
  - large stomach  
  ✅ large intestine  
  - small stomach  
  - small intestine  
  _Recall; 'large/small stomach' silly; question leaks 'wider', 'shorter' clues._

**bio_heart [ft] score 2 key OK SENSIBLE H1 H6**: Where is the heart located in the body?  
  - in the abdomen  
  - in the lungs  
  ✅ in the chest  
  - in the brain  
  _Plain recall; 'chest' is directly stated. Distractors are easy, not diagnostic._

**bio_heart [ft] score 2 key OK not sensible H1 H4 H6 H5**: What part of the heart receives blood that has given its oxygen to the body and sends it to the lungs?  
  ✅ the right side  
  - the back side  
  - the left side  
  - the front side  
  _Recall; question leaks via 'receives blood'; 'back/front side' distractors are implausible._

**bio_heart [ft] score 2 key OK SENSIBLE H1 H4**: What is the normal pulse rate for a healthy adult at rest?  
  - 60 beats per minute  
  - 90 beats per minute  
  ✅ 72 beats per minute  
  - 80 beats per minute  
  _Pure number recall; distractors are arbitrary nearby numbers, only one is passage-based._

**bio_microbes [ft] score 2 key OK not sensible H1 H4 H5**: What is the name of the microorganism used in making bread, idli and dosa batter?  
  ✅ yeast  
  - mold  
  - bacteria  
  _Recall; only three options; 'mold' and 'bacteria' weak; yeast wording copied._

**bio_microbes [ft] score 2 key OK not sensible H1 H4 H5**: In 1929, what did alexander Fleming notice that a mould growing on one of his plates had stopped?  
  ✅ the growth of bacteria  
  - the growth of algae  
  - the growth of fungi  
  _Recall of Fleming sentence; three options only; answer copies passage wording._

**bio_pitcher [ft] score 2 key OK SENSIBLE H1 H2 H6 H7 H8**: Pitcher plants grow in soil that is poor in what nutrient, which is needed for plants to make proteins?  
  ✅ nitrogen  
  - carbon  
  - potassium  
  - phosphorus  
  _Recall; question gives away context; wordy; options are plausible nutrients but no why-reasoning._

**bio_pitcher [ft] score 2 key OK not sensible H1 H4 H6**: What do the pitcher plant carry out in its green leaves?  
  - digestion  
  - respiration  
  ✅ photosynthesis  
  _Recall; only 3 options; grammar error 'do'; photosynthesis is the only plant-food option._

**bio_pitcher [ft] score 1 KEY WRONG not sensible H1 H3 H4 H5**: What is the rim of a pitcher made of?  
  - wood  
  - metal  
  - glass  
  ✅ slippery  
  _Passage says slippery, not material; key is a quality, not a material; options mismatched._

**bio_pitcher [ft] score 1 key OK not sensible H1 H2 H3 H4 H5 H6**: Most green plants make their own food, but a few plants also trap what?  
  - animals  
  - animals and insects  
  ✅ insects  
  - plants  
  _Fill-in-blank recall; 'animals and insects' also arguably true; passage sentence copied verbatim._

**bio_pollination [ft] score 2 key OK SENSIBLE H1 H4 H8**: What is the name of the sticky top of the pistil?  
  - the pollen grain  
  - the pollen  
  - the pollen sac  
  ✅ the stigma  
  _Pure recall of a defined term; distractors are all pollen-related names; no explanation given._

**bio_pollination [ft] score 1 key OK not sensible H1 H3 H4 H5 H6 H8**: What is the term for when pollen is carried to a flower on another plant of the same kind?  
  ✅ cross-pollination  
  - cross-arrangement  
  - cross-singulation  
  _Only 3 options; 'cross-' options are nonsense; term recall; question leaks the key words._

**bio_pollination [ft] score 1 KEY WRONG not sensible H1 H3 H4 H5 H6 H8**: What do bees and butterflies do to drink nectar?  
  ✅ They visit flowers  
  - They drink from flowers  
  - They eat flowers  
  _Only 3 options; 'visit' and 'drink' both fit; wording leaks; recall._

**bio_pollination [ft] score 2 key OK SENSIBLE H1 H4 H6 H7 H8**: After pollination, the pollen grain grows a tube down to the ovule, and the male cell joins the egg cell. this is called what?  
  - migration  
  ✅ fertilization  
  - reproduction  
  - propagation  
  _Term recall from the passage; weak distractors; stray lowercase; spelling differs; no explanation._

**bio_respiration [ft] score 2 key OK SENSIBLE H1 H2**: During hard exercise, our leg muscles may respire anaerobically and produce what?  
  - carbon dioxide  
  ✅ lactic acid  
  - hydrogen  
  - carbon monoxide  
  _Pure recall, fill-in-blank style 'produce what?'; answer can be word-spotted._

**bio_respiration [ft] score 2 key OK not sensible H1 H4 H6**: What do plants do all the time, day and night?  
  - they breathe  
  - they sleep  
  - they breathe in  
  ✅ they respire  
  _Recall; 'breathe' options are weak, and 'respire' is leaked by the passage wording._

**bio_respiration [ft] score 2 key OK not sensible H1 H4 H6 H7**: What is the name of the process in which glucose is broken down completely into carbon dioxide and water?  
  ✅ aerobic respiration  
  - anaerobic respiration  
  - aerobic digestion  
  - aerobic metabolism  
  _Recall of a term; question leaks the definition, and the 'aerobic' distractors are weak, and the question runs over 25 words._

**bio_respiration [ft] score 3 key OK SENSIBLE H4**: During the day, what is the respiration of plants doing?  
  - It is being released  
  - It is not happening  
  - It is being used  
  ✅ It is hidden  
  _Tests understanding of hidden respiration, but the distractors are vague and not tied to clear misconceptions._

**bio_vaccine [ft] score 2 key OK not sensible H1 H4**: Who noticed something interesting in the countryside?  
  - A teacher  
  ✅ A doctor  
  - A farmer  
  - A student  
  _Pure recall; 'doctor' is the only plausible role, distractors are implausible._

**bio_vaccine [ft] score 2 key OK SENSIBLE H1 H4**: What was one of the most feared diseases in the world in the eighteenth century?  
  - malaria  
  ✅ smallpox  
  - tuberculosis  
  - influenza  
  _Pure recall of a named disease; distractors are other diseases not in passage._

**bio_vaccine [ft] score 1 KEY WRONG not sensible H3 H1 H4**: How many weeks did Jenner take to expose the boy to smallpox?  
  - Three  
  - One  
  - Four  
  ✅ Two  
  _Passage says only 'some weeks later'; no exact number, so key D is unprovable._

**bio_vaccine [ft] score 2 key OK SENSIBLE H1 H6 H4**: What contains dead or weakened germs, or parts of them?  
  ✅ a vaccine  
  - a treatment  
  - a drug  
  - a medicine  
  _Recall of a definition sentence; question wording is copied from the passage._

**bio_xylem [ft] score 2 key OK SENSIBLE H1 H2 H4**: Together, xylem and phloem form the vascular bundles that can be seen as what?  
  - trunks  
  - arteries  
  - roots  
  ✅ veins  
  _Pure recall of a phrase; 'arteries' is the only plausible distractor, trunks/roots weak._

**bio_xylem [ft] score 2 key OK SENSIBLE H1 H3 H4**: What is the main force that pulls water up through the roots?  
  ✅ transpiration  
  - convection  
  - evaporation  
  - diffusion  
  _Recall; 'through the roots' is wrong (pulled up from roots); evaporation is also arguable._

**bio_xylem [ft] score 2 key OK SENSIBLE H1 H4 H6**: What is the name of the second tissue that carries food made in the leaves to other parts of the plant?  
  - the root  
  - the xylem  
  - the bark  
  ✅ the phloem  
  _Recall; the question leaks 'second tissue' and options are weak distractors._

**chem_acids [ft] score 2 key OK SENSIBLE H1 H4 H6**: What color does blue litmus paper turn in an acid?  
  - blue  
  - green  
  ✅ red  
  - yellow  
  _Pure recall of a stated fact; distractors are just other colours, not misconceptions._

**chem_acids [ft] score 2 key OK SENSIBLE H1 H4**: What is injected into the skin when an ant bite occurs?  
  - sodium carbonate  
  ✅ formic acid  
  - sodium chloride  
  - sodium hydroxide  
  _Plain recall; distractors are unrelated chemicals (sodium ones) not from passage misconceptions._

**chem_acids [ft] score 2 key OK SENSIBLE H1 H4 H5**: What is a safe way to test a substance?  
  - using a scale  
  - tasting  
  ✅ using indicators  
  - using a pH meter  
  _Recall; 'tasting' is the obvious wrong pick; correct option uses passage wording; the scale and pH meter are weak._

**chem_acids [ft] score 2 key OK SENSIBLE H1 H4**: What color does a turmeric stain turn when soap is rubbed on it?  
  ✅ red  
  - yellow  
  - green  
  - blue  
  _Recall of stated colour; distractors are just other colours. Fourth recall question breaks the 1-in-4 limit._

**chem_changes [ft] score 2 key OK not sensible H1 H2 H4 H6**: What kind of change is when a substance changes its shape, size or state, but no new substance is formed?  
  - biological change  
  ✅ physical change  
  - chemical change  
  _Pure recall of definition; question leaks 'physical'; only 3 options; 'biological' is silly._

**chem_changes [ft] score 1 key OK not sensible H1 H3 H4 H5**: What happens when a piece of paper burns?  
  ✅ it turns into ash, smoke and gases  
  - it turns into a new substance  
  - it turns into a new type of material  
  - it turns into a new type of substance  
  _B, C, D are near-duplicates and also true of burning paper; two-correct ambiguity._

**chem_combustion [ft] score 2 key OK SENSIBLE H1 H2 H4 H6**: Combustion is a chemical process in which a substance reacts with what to give off heat?  
  - nitrogen  
  - carbon  
  - hydrogen  
  ✅ oxygen  
  _Pure recall, fill-in-blank style; no explanation; weak distractors; passage wording copied._

**chem_combustion [ft] score 2 key OK SENSIBLE H1 H4 H6 H8**: What is the name of the substance that cools the burning material below its ignition temperature?  
  ✅ water  
  - oxygen  
  - carbon  
  - nitrogen  
  _Recall question; distractors are random chemicals; no explanation; 2 recall already too many._

**chem_combustion [ft] score 1 key OK not sensible H1 H3 H4 H8**: What kind of fuel has a low ignition temperature, so it catches fire easily?  
  - gasoline  
  - coal  
  ✅ kerosene  
  _Only three options; recall; gasoline is petrol-like and its ignition temperature is not stated._

**chem_metals [ft] score 1 key OK not sensible H1 H2 H4 H5 H7**: What are good conductors of heat and electricity?  
  ✅ metals  
  - metals and wood  
  - metals and glass  
  _Pure recall, only 3 options, silly distractors, 'what are' is vague._

**chem_metals [ft] score 2 key OK not sensible H1 H4**: Graphite is a form of what element?  
  - oxygen  
  - nitrogen  
  ✅ carbon  
  - hydrogen  
  _Plain recall; distractors are random elements, not misconceptions._

**chem_metals [ft] score 1 key OK not sensible H1 H2 H4 H5 H6**: Metals form oxides that are basic in nature, while non-metals form oxides that are what?  
  ✅ acidic  
  - neutral  
  - basic  
  _Fill-in-the-blank recall; only 3 options; 'basic' repeats the question wording._

**chem_metals [ft] score 1 key OK not sensible H1 H2 H3 H4 H5**: What are malleable and ductile?  
  - metals and glass  
  ✅ metals  
  - metals and plastics  
  - metals and wood  
  _Vague stem; 'metals' is the only non-compound option, so it is guessable; recall._

**chem_separation [ft] score 2 key OK not sensible H1 H2 H4 H6**: What is the name of the process in which a mixture of sand and water settles at the bottom?  
  - evaporation  
  ✅ sedimentation  
  - precipitation  
  - dissolution  
  _Recall of a term; 'settles' leaks sedimentation; precipitation/dissolution weak distractors._

**chem_separation [ft] score 2 key OK not sensible H1 H4 H5 H6**: What is the name of the process of pouring off clear water into another vessel without disturbing the sand?  
  ✅ decantation  
  - sedimentation  
  - filtration  
  _Only three options; recall of term; question text gives definition._

**chem_separation [ft] score 2 key OK not sensible H1 H4 H5**: In villages, husk is separated from grain by what process?  
  - sorting  
  - drying  
  ✅ winnowing  
  _Three options only; recall; sorting and drying are weak distractors._

**civ_bill [ft] score 1 key OK not sensible H1 H3 H4 H5**: What can be introduced by a minister?  
  - A law  
  ✅ A bill  
  - A proposal  
  - A rule  
  _Recall; 'proposal' and 'law' arguably also fit, since a bill is a proposal._

**civ_bill [ft] score 2 key OK SENSIBLE H1 H4 H6**: What is the name of the body that makes laws for the whole country?  
  - the Rajya Sabha  
  ✅ Parliament  
  - the House of Lords  
  - the Lok Sabha  
  _Pure recall; 'House of Lords' is outside the passage, though Parliament stands out as a general term._

**civ_bill [ft] score 2 key OK not sensible H1 H3 H4 H6**: In India, what can be introduced only in the Lok Sabha?  
  ✅ A money bill  
  - A bill for the government  
  - A tax bill  
  - A bill for the people  
  _Recall; 'tax bill' is effectively also a money bill, so A and C overlap._

**civ_bill [ft] score 2 key OK SENSIBLE H1 H4**: What happens first when a bill is introduced in a house?  
  ✅ It is read out and introduced  
  - It is voted  
  - It is debated  
  - It is passed  
  _Sequence recall; wording copies the passage and the distractors are later stages._

**civ_panchayat [ft] score 1 KEY WRONG not sensible H1 H3 H4 H6**: What is the name of the organization that works at the district level?  
  - Panchayat  
  - Gram Panchayats  
  ✅ Panchayat Samiti  
  - Zila Parishad  
  _Key C is wrong; Zila Parishad is district level. Plain recall._

**civ_panchayat [ft] score 2 key OK not sensible H1 H4 H6**: Every adult who lives in the village and whose name is on the voters' list is a member of what?  
  - the House of Representatives  
  ✅ the Gram Sabha  
  - the Parliament  
  - the Council  
  _Key right but pure recall; question leaks Gram Sabha wording; distractors unrelated, implausible._

**civ_rights [ft] score 2 key OK SENSIBLE H1 H6 H4 H8**: What are the basic rights given to every citizen in India?  
  - Right to Property  
  ✅ Fundamental Rights  
  - Right to Vote  
  - Right to Education  
  _Recall; the key words are in the question. Distractors are outside the passage. No explanation._

**civ_rights [ft] score 1 KEY WRONG not sensible H1 H2 H3 H4 H8**: What is the name of the right?  
  - Right to Property  
  ✅ Right to Equality  
  - Right to Freedom  
  - Right to Protection  
  _Vague stem, 'the right' is undefined; no unique answer._

**civ_secularism [ft] score 2 key OK not sensible H1 H4 H5 H6**: What law is in effect in India?  
  - The law requires people riding two-wheelers to wear sunglasses  
  - The law requires people riding two-wheelers to wear hats  
  - The law requires people riding two-wheelers to wear glasses  
  ✅ The law requires people riding two-wheelers to wear helmets  
  _Pure recall; option D echoes the passage; distractors silly (sunglasses, hats, glasses); vague question._

**eco_money [ft] score 1 key OK not sensible H1 H4 H8**: How much of the deposits do banks keep as cash?  
  - 20%  
  - 10%  
  ✅ 15%  
  _Pure number recall; only three options; 10% and 20% are arbitrary._

**eco_money [ft] score 2 key OK not sensible H1 H2 H5 H4**: What has been used as money over history?  
  ✅ grains, cattle, shells, and coins  
  - paper notes and coins  
  - paper notes and gold  
  - gold, silver and copper  
  _Recall; A is longest list and combines items; B, C, D partly true._

**eco_money [ft] score 2 key OK SENSIBLE H1 H4 H6**: What was the system before money was used?  
  ✅ the barter system  
  - the trade system  
  - the exchange system  
  - the market system  
  _Plain recall; distractors are invented system names; passage wording matches only the key._

**eco_money [ft] score 1 key OK not sensible H1 H4 H6**: What is the name of the medium of exchange?  
  - grain  
  - shoes  
  ✅ money  
  - wheat  
  _Leaks the answer: 'medium of exchange' defines money; distractors are silly goods._

**eco_shg [ft] score 1 KEY WRONG not sensible H1 H3 H4 H5**: What do banks ask for in order to get loans?  
  ✅ Collateral  
  - Land  
  - Money  
  - Credit  
  _Collateral and land both fit (land is an example); pure recall; weak distractors._

**eco_unemployment [ft] score 1 KEY WRONG not sensible H1 H3 H4**: How many people are working on the farm?  
  - Two  
  - Five  
  ✅ Three  
  - Four  
  _Key C (Three) is wrong; five work on the farm. Recall, miskeyed._

**env_solar [ft] score 1 key OK not sensible H1 H4 H5 H6 H7**: What is the main source of energy for the earth?  
  ✅ the sun  
  - the earth  
  - the moon  
  _Pure recall, answer leaked by the passage's first sentence, only 3 options, silly distractors._

**env_solar [ft] score 1 KEY WRONG not sensible H1 H3 H4**: How many cells are joined together in a solar panel?  
  - 100  
  - 1000  
  ✅ 10  
  - 10000  
  _The passage never states how many cells a panel has, so key C is unsupported._

**env_waste [ft] score 1 KEY WRONG not sensible H1 H3 H4**: What can be recycled?  
  - Plastic bags  
  - Paper  
  - Plastic bottles  
  ✅ Glass and metal  
  _Paper and glass and metal are all recyclable; several options are correct._

**env_waste [ft] score 2 key OK not sensible H1 H4 H6**: What do you call the huge, smelly mountains of garbage that attract flies and rats?  
  - waste  
  ✅ landfills  
  - waste dumps  
  - garbage  
  _Term recall; question restates passage wording; distractors are weak, overlapping terms._

**geo_ghats [ft] score 2 key OK SENSIBLE H1 H3 H4 H5 H6**: What is the name of the region that receives heavy rain from the south-west monsoon?  
  - The Eastern Monsoon  
  ✅ The Western Ghats  
  - The Western Monsoon  
  - The Eastern Ghats  
  _Pure recall; 'Western Ghats' echoed in option; distractors are word swaps of the answer._

**geo_ghats [ft] score 1 key OK not sensible H1 H4 H5 H6**: What is the name of the chain of mountains running parallel to the western coast of India?  
  - the Himalayas  
  - the Andes  
  ✅ the Western Ghats  
  _Only 3 options; recall; question text nearly names the answer; Andes silly._

**geo_ghats [ft] score 1 key OK not sensible H1 H2 H4 H5 H8**: UNESCO declared what in 2012?  
  - the Eastern Ghat  
  ✅ the Western Ghats  
  - the Western Ghat  
  - the Eastern Ghats  
  _Fill-in-blank style recall; distractors differ only by Eastern/singular spelling._

**geo_groundwater [ft] score 1 key OK not sensible H1 H4 H5 H6 H7**: What is the name of the water that fills the tiny spaces between grains of sand and soil, and the cracks in rocks?  
  - surface water  
  - ocean water  
  ✅ groundwater  
  _Recall; only 3 options; distractors silly; question leaks the answer's definition._

**geo_groundwater [ft] score 1 key OK not sensible H1 H4 H6**: What is a layer of rock or soil that stores water and allows it to flow through called?  
  ✅ an aquifer  
  - a sedimentary  
  - a sediment  
  - a sedimentary rock  
  _Pure definition recall; options are off-topic rock terms, two near-duplicates._

**geo_groundwater [ft] score 1 key OK not sensible H1 H4 H5**: What do we call water that is found at some depth below the ground?  
  - ocean water  
  ✅ groundwater  
  - surface water  
  _Recall; only 3 options; distractors unrelated to any misconception._

**geo_groundwater [ft] score 1 key OK not sensible H1 H4 H5**: What is the name of the process in which water moves down until it reaches a layer of rock that it cannot pass through?  
  ✅ infiltration  
  - erosion  
  - evaporation  
  _Name-recall; 3 options; distractors from other topics, not passage misconceptions._

**geo_monsoon [ft] score 2 key OK not sensible H1 H3 H4 H5 H6**: What winds blow from high pressure to low pressure?  
  - dry winds  
  - cold winds  
  ✅ moist winds  
  _Recall; only 3 options; 'moist' appears in passage; cold winds weak distractor._

**geo_monsoon [ft] score 2 key OK not sensible H1 H2 H4 H5 H6**: When the moist winds are forced to rise over the western ghats, they cool and drop heavy rain on what?  
  ✅ the western slopes  
  - the southern slopes  
  - the eastern slopes  
  _Recall; 3 options; question text leaks 'western' into the answer._

**geo_monsoon [ft] score 2 key OK not sensible H1 H4 H6**: What happens in May in India?  
  - A high pressure area forms over the plains of south-western India  
  - A high pressure area forms over the plains of north-western India  
  - A low pressure area forms over the plains of south-western India  
  ✅ A low pressure area forms over the plains of north-western India  
  _Recall of phrase; distractors are only word swaps; question leaks 'May' context._

**geo_monsoon [ft] score 2 key OK not sensible H1 H4**: What do these winds pick up as they cross the warm ocean?  
  - water  
  - heat  
  - wind  
  ✅ moisture  
  _Pure recall; 'water' also arguably correct; distractors weak and nonsensical._

**geo_seasons [ft] score 1 KEY WRONG not sensible H1 H3 H4**: What is the name of the movement of the earth?  
  - expansion  
  ✅ rotation  
  - revolution  
  - contraction  
  _Ambiguous: rotation and revolution both movements; key B arbitrary, vague question_

**geo_seasons [ft] score 1 KEY WRONG not sensible H3 H4 H6**: Why do many people believe that summer comes because the earth moves closer to the sun?  
  - Because the earth is closest to the sun in early winter  
  - Because the earth is closest to the sun in early spring  
  - Because the earth is closest to the sun in early summer  
  ✅ Because the earth is closest to the sun in early January  
  _Question asks why people believe; options state closest date. Key D mismatches question, illogical_

**geo_seasons [ft] score 2 key OK SENSIBLE H1 H4 H5**: How many days does it take for the earth to complete one orbit around the sun?  
  ✅ 365 days  
  - 368 days  
  - 366 days  
  - 367 days  
  _Plain recall; key correct but 365 omits the 6 hours; distractors are bare numbers_

**geo_soils [ft] score 2 key OK not sensible H1 H2 H4 H5**: Laterite soil forms in areas with high temperature and what else?  
  - snow  
  ✅ rainfall  
  - precipitation  
  - wind  
  _Fill-in-the-blank recall; 'precipitation' also arguably correct (synonym of rainfall); weak distractors._

**geo_soils [ft] score 2 key OK not sensible H1 H4 H6 H5**: Where is the most widespread alluvial soil?  
  ✅ in the northern plains  
  - in the southern plains  
  - in the southern part of the world  
  - in the northern part of the world  
  _Pure recall; 'northern plains' leaks; distractors are silly geographic variants._

**geo_soils [ft] score 1 key OK not sensible H1 H6 H4 H7**: What is formed when rocks are slowly broken down by changes in temperature, running water, wind and living things, over thousands of years?  
  - water  
  ✅ soil  
  - rock  
  - atmosphere  
  _Answer 'soil' obvious from passage topic; question too long; trivial distractors; recall._

**geo_soils [ft] score 2 key OK not sensible H1 H4 H5 H6**: What type of soil is found in the eastern and southern parts of the deccan?  
  ✅ red and yellow soils  
  - white soil  
  - black soil  
  - yellow soil  
  _Recall; correct option longest and copies passage; 'yellow soil' partially correct; weak distractors._

**geo_sundarbans_ocr [ft] score 2 key OK SENSIBLE H1 H6**: How many times a day does the tides flood the forest floor with sea water?  
  - Three times a day  
  - Once a day  
  ✅ Twice a day  
  - Four times a day  
  _Pure recall of 'twice a day'; grammar error 'does'; distractors are bare numbers._

**his_1857 [ft] score 1 KEY WRONG not sensible H1 H3 H4**: How many troops did the British bring in?  
  - Two  
  - Four  
  - One  
  ✅ Three  
  _Passage gives no number of troops; recall, unanswerable, arbitrary options._

**his_1857 [ft] score 2 key OK not sensible H1 H4 H5 H6**: In 1858, what happened to the East India Company?  
  - The British Parliament ended the rule of the British Crown  
  ✅ The British Parliament ended the rule of the East India Company  
  - The British Crown took direct control of India  
  _Recall, only 3 options, answer restates question, distractors are silly._

**his_1857 [ft] score 2 key OK SENSIBLE H1 H4**: Where did the sepoys march to on 10 May?  
  ✅ Delhi  
  - Barrackpore  
  - Mumbai  
  - Meerut  
  _Plain recall; Meerut and Barrackpore are plausible distractors, Mumbai is weak._

**his_1857 [ft] score 2 key OK SENSIBLE H1 H4 H6**: What was the biggest challenge to British rule in India in the nineteenth century?  
  - The revolt of 1868  
  ✅ The revolt of 1857  
  - The revolt of 1867  
  - The revolt of 1858  
  _Recall, near-verbatim from first sentence; distractors are only wrong years._

**his_ashoka [ft] score 2 key OK not sensible H1 H4**: Who was the wise minister of Ashoka?  
  - Ashoka  
  - Chandragupta Maurya  
  ✅ Chanakya  
  - Surya  
  _Pure recall; distractors are names in passage or silly (Surya)._

**his_ashoka [ft] score 1 KEY WRONG not sensible H1 H3 H4 H5**: How long did Ashoka fight a war?  
  - About 268 BCE  
  ✅ About eight years  
  - About 268 AD  
  _Passage gives no war duration; 'eight years' is gap before war; only 3 options._

**his_ashoka [ft] score 2 key OK not sensible H1 H4 H5**: What did Ashoka do after the war?  
  ✅ He was filled with sorrow  
  - He was filled with pride  
  - He was filled with anger  
  - He was filled with joy  
  _Sorrow is supported, but this is recall; distractors are arbitrary emotions; and Q asks 'do', not feel._

**his_chola [ft] score 2 key OK not sensible H1 H2 H6 H7**: What was the Chola's main function?  
  - They were the main centres of trade  
  - They were the main centres of worship  
  ✅ They were the main centres of town life  
  - They were the main centres of education  
  _Garbled stem ('Chola's main function'); temples never named; recall; 'worship' and 'centres of town life' both plausible._

**his_chola [ft] score 2 key OK SENSIBLE H1**: Who became king in 985 CE?  
  - Rajaraja II  
  ✅ Rajaraja I  
  - Rajendra I  
  - Rajaraja III  
  _Pure recall of a name/date; key correct; distractors only nearby names._

**his_chola [ft] score 2 key OK SENSIBLE H1 H5 H6**: When the clay is heated, what happens to the wax?  
  - it becomes more liquid  
  ✅ it melts and flows out  
  - it becomes more viscous  
  - it becomes more solid  
  _Near-verbatim recall; key copies passage wording; 'melts' leaked by the question's heating context._

**his_dandi [ft] score 2 key OK not sensible H1 H4 H6**: How long did Gandhi walk?  
  ✅ 24 days  
  - 18 days  
  - 12 days  
  - 16 days  
  _Plain recall; distractors are arbitrary numbers, not misconceptions. Key is correct._

**his_dandi [ft] score 2 key OK not sensible H1 H4 H5**: What did Gandhi do on 6 April 1930?  
  ✅ He broke the salt law  
  - He helped the government  
  - He helped the poor  
  - He helped the people  
  _Recall; wrong options are vague 'helped' variants, only correct one is specific._

**his_dandi [ft] score 1 key OK not sensible H1 H3 H4 H6**: What did India struggle for in 1930?  
  - Education  
  - Food  
  - Salt  
  ✅ Freedom  
  _Passage says salt was the centre of the struggle for freedom; question is ambiguous and recall._

**his_dandi [ft] score 1 KEY WRONG not sensible H1 H3 H4 H5**: What did people do in the US?  
  - They made money from the sea  
  ✅ They made salt from sea water  
  - They made money from the sea water  
  _US is not in the passage; 3 options; B is the only sensible one._

**his_harappa [ft] score 1 KEY WRONG not sensible H1 H2 H3 H4 H5 H6 H7 H8**: How many cities were discovered in the Indus Valley?  
  - 4,700  
  - 4,700 years  
  ✅ 4,700 years ago  
  _Passage never gives a count of cities; options are nonsense numbers/years; only 3 options, no explanation._

**his_harappa [ft] score 1 KEY WRONG not sensible H1 H3 H4 H5 H7 H8**: What kind of drains were in the cities?  
  ✅ The streets and the drains  
  - The streets  
  - The streets and the houses  
  _Incoherent options; passage says drains run along streets and connect to houses; key unprovable._

**his_mughal [ft] score 1 KEY WRONG not sensible H1 H3 H4**: How many horsemen did Mansabdars have to maintain?  
  - 1000  
  - 100  
  - 10000  
  ✅ 10  
  _Passage says 'fixed number' only; no figure given, so key D is unsupported._

**phy_circuit [ft] score 2 key OK SENSIBLE H1 H4**: How many things do you need for a simple electric circuit?  
  - two  
  ✅ three  
  - four  
  - one  
  _Pure recall of a count; distractors are arbitrary numbers, not misconceptions._

**phy_circuit [ft] score 1 key OK not sensible H1 H2 H4 H6 H7**: When two or more cells are joined, the positive terminal of one cell must be connected to the negative terminal of the next. this arrangement is called what?  
  ✅ a battery  
  - a circuit board  
  - a circuit  
  - a battery pack  
  _Question copies passage and leaks answer context; 'battery pack' is near-duplicate; too long._

**phy_circuit [ft] score 2 key OK SENSIBLE H1 H4**: How many terminals does a cell have?  
  - three  
  - four  
  ✅ two  
  - one  
  _Plain recall; distractors are arbitrary numbers._

**phy_friction [ft] score 1 key OK not sensible H1 H3 H4 H5 H6**: What happens when you push a heavy box across the floor?  
  - It slides until it stops and then stops  
  - It slides forever  
  ✅ It slides until it stops  
  - It slides until it stops and then goes back  
  _Recall; A and C both say it stops (two correct); silly distractors; leaks key._

**phy_friction [ft] score 2 key OK not sensible H1 H4 H6**: What happens when you rub your palms together quickly?  
  ✅ They become warm  
  - They become cold  
  - They become hot  
  _Plain recall; only 3 options; 'hot' and 'cold' weak; 'warm' leaked._

**phy_friction [ft] score 1 KEY WRONG not sensible H1 H3 H4 H5 H7**: What is the friction between a polished marble floor and a rough brick floor?  
  - less  
  - equal  
  ✅ more  
  - same  
  _Garbled; marble gives less than brick, but 'more' is ambiguous; C and A are plausible._

**phy_friction [ft] score 2 key OK SENSIBLE H1 H4 H5**: What is put between the moving parts of machines?  
  - oil and sand  
  - water and grease  
  - oil and water  
  ✅ oil and grease  
  _Pure recall; D is the only option matching the passage; distractors are arbitrary._

**phy_magnets [ft] score 1 key OK not sensible H1 H2 H4 H5 H6**: What are stored in pairs with their unlike poles on the same side, separated by a piece of wood?  
  - barometers  
  ✅ bar magnets  
  - magnetometers  
  _Only 3 options; recall; silly distractors; question contains the passage wording._

**phy_mirror [ft] score 1 KEY WRONG not sensible H1 H3 H4**: How far is the image from the mirror?  
  - 3 metres  
  - 2 metres  
  - 1 metre  
  ✅ 4 metres  
  _Image is 2 m behind mirror; key says 4 m (distance from you). Key wrong._

**phy_mirror [ft] score 1 KEY WRONG not sensible H1 H3 H5 H6 H7**: What is the name of the line drawn at the point where the light hits the mirror, standing straight up from the surface at 90 degrees?  
  ✅ normal  
  - normal line  
  - incident  
  - reflected  
  _A and B both correct; question copies passage and leaks answer; too long._

**phy_mirror [ft] score 3 key OK SENSIBLE H1 H5**: If a ray strikes a mirror at an angle of incidence of 30 degrees, what happens?  
  - it is reflected at 60 degrees  
  ✅ it is reflected at 30 degrees  
  - it is reflected at 120 degrees  
  - it is reflected at 90 degrees  
  _Key correct; near-recall of the passage example; distractors plausible but weak._

**phy_mirror [ft] score 2 key OK SENSIBLE H1 H6**: What kind of mirror forms an image that is upright and of the same size as the object?  
  - a curved mirror  
  ✅ a plane mirror  
  - a concave mirror  
  - a convex mirror  
  _Key correct; recall by phrase matching; 'plane mirror' leaks via passage; distractors from outside passage._

**phy_pressure [ft] score 2 key OK SENSIBLE H1 H4 H5**: What is the effect of a sharp edge on a knife?  
  - the force is greater  
  ✅ the pressure is greater  
  - the pressure is less  
  - the force is less  
  _Key right (greater pressure), but options are simple recall; 'force' distractors weak._

**phy_sound [ft] score 1 key OK not sensible H1 H2 H4 H5 H6 H7**: What are stretched across the windpipe, and air from the lungs makes them vibrate?  
  ✅ vocal cords  
  - vocal folds  
  - vocal trills  
  _Fill-in-the-blank style recall; only 3 options; 'vocal folds' arguably plausible; trivial distractors._

**phy_sound [ft] score 1 KEY WRONG not sensible H1 H3 H4 H5**: What do you call a high-pitched sound, like a whistle, and a low-pitched sound, like a drum?  
  - high sound  
  ✅ high frequency  
  - low sound  
  - low frequency  
  _Passage says high frequency gives high pitch; 'pitch' is the real answer and is absent. Key B wrong._

**phy_sound [ft] score 1 key OK not sensible H1 H3 H4 H5 H6 H8**: What do you hear when you pluck the string of a sitar?  
  ✅ a sound  
  - a vibration  
  - a noise  
  _Trivial recall; 3 options; 'a noise' and 'a sound' ambiguous; no explanation._

**phy_sound [ft] score 1 key OK not sensible H1 H2 H4 H8**: What can travel through solids, liquids and gases, but cannot travel through a vacuum?  
  - heat  
  ✅ sound  
  - electricity  
  - light  
  _Pure recall of a phrase; question leaks passage wording; distractors not misconception-based; no explanation._
