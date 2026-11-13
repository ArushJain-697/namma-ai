# Backup quiz (plain Qwen3-0.6B, one call per question) on the 40 eval passages

Judge: Sonnet against docs/QUESTION_RUBRIC.md, blind to variant and to kept/rejected.

| Variant | Passages with >= 3 questions | Questions shown | Key correct | Score >= 4 (good) | Score <= 2 (bad) | Pi time per quiz (est. 60/20 tok/s), median / max |
|---|---|---|---|---|---|---|
| hybrid | 27/40 | 121 | 80/121 | 1/121 | 115/121 | 58.1 s / 75.3 s |
| hybrid_mis | 31/40 | 125 | 91/125 | 2/125 | 106/125 | 61.9 s / 77.3 s |
- **hybrid: sensible 12/121** (key right, all options on topic and grammatical, answer not obvious; the lower, practical bar)
- **hybrid_mis: sensible 24/125** (key right, all options on topic and grammatical, answer not obvious; the lower, practical bar)

## Did the self-check help? (rejected-by-self-check questions vs shown ones, same judge)

- hybrid: questions the self-check threw out had a correct key 7/20 times, score >= 4 in 0/20
- hybrid_mis: questions the self-check threw out had a correct key 7/20 times, score >= 4 in 0/20

## Why questions were rejected

- hybrid: answer is clearly the longest option x1
- hybrid: answer only repeats the question x23
- hybrid: answer too long x44
- hybrid: not enough wrong options x6
- hybrid: self-check failed x20
- hybrid_mis: answer only repeats the question x24
- hybrid_mis: answer too long x45
- hybrid_mis: not enough wrong options x6
- hybrid_mis: self-check failed x20

## Every shown question with its grade

**bio_digestion [hybrid_mis] score 3 key OK SENSIBLE H6 H4**: Why does the inner lining of the stomach release hydrochloric acid and digestive juices?  
  - Because bile is produced by the stomach to digest all types of food  
  ✅ Because the acid kills bacteria that enter with the food  
  - Because food is converted into energy inside the stomach  
  - Because digestion only happens in the stomach  
  _Key correct, but 'acid' and 'bacteria' leaked; distractors weak/silly ('only in stomach')._

**bio_digestion [hybrid] score 1 KEY WRONG not sensible H3 H6 H4**: Why does the inner lining of the stomach release hydrochloric acid and digestive juices?  
  - Because the juices begin to break down proteins  
  - Because the partly digested food passes into the small intestine  
  ✅ Because the acid kills bacteria that enter with the food  
  - Because the stomach is a thick-walled bag  
  _A and C both supported by passage; C leaks 'acid'; B/D unrelated._

**bio_digestion [hybrid_mis] score 2 key OK not sensible H3 H4 H5 H6**: Why does the food pass from the stomach to the small intestine?  
  ✅ Because it is digested and processed by the small intestine  
  - Because food is converted into energy inside the stomach  
  - Because bile is produced by the stomach to digest all types of food  
  - Because villi are tiny hairs that filter out waste from the food  
  _Key is circular, leaks 'small intestine', only on-topic option; distractors off-topic/false._

**bio_digestion [hybrid] score 2 key OK SENSIBLE H1 H6 H5**: Why do we chew food?  
  - Because the partly digested food passes into the small intestine  
  ✅ Because our teeth break food into small pieces  
  - Because the juices begin to break down proteins  
  - Because undigested food moves into the large intestine  
  _Pure recall; 'break food' leaked from question; key copies passage wording, distractors are other sentences._

**bio_digestion [hybrid_mis] score 2 key OK SENSIBLE H1 H6 H5 H4**: Why do we chew food?  
  - Because villi are tiny hairs that filter out waste from the food  
  ✅ Because our teeth break food into small pieces  
  - Because saliva only makes food slippery  
  - Because bile is produced by the stomach to digest all types of food  
  _Recall with leak; distractors implausible; correct option only sensible fit._

**bio_heart [hybrid_mis] score 1 KEY WRONG not sensible H3 H4 H5 H6**: Why is the pulse rate higher in children?  
  - Because each contraction of the heart is a heartbeat  
  ✅ Because they have a higher heart rate at rest  
  - Because the blood in them is under high pressure  
  - Because pulse and heartbeat are two completely different and unrelated processes  
  _Passage gives no reason for the higher rate. B restates the question, and D is silly._

**bio_heart [hybrid] score 2 KEY WRONG not sensible H3 H4 H5 H6**: Why do blood vessels in the heart have thick, elastic walls?  
  - Because oxygen-rich blood returns to the left side of the heart  
  ✅ Because the blood is under high pressure and flows in only one direction  
  - Because the heart beats faster to supply more oxygen to the muscles  
  - Because the heart is a muscular organ about the size of your fist  
  _Question says heart vessels; passage says arteries. B is half-right, but the one-way flow is the valves' job._

**bio_heart [hybrid] score 1 KEY WRONG not sensible H3 H4 H5 H6**: Why is the pulse rate higher in children?  
  ✅ Because they have a higher heart rate at rest  
  - Because the blood in them is under high pressure  
  - Because each contraction of the heart is a heartbeat  
  - Because blood returns to the heart through veins  
  _Passage never explains why children's rate is higher. A just restates the question, and the other options are irrelevant._

**bio_heart [hybrid_mis] score 2 KEY WRONG not sensible H3 H4 H5 H6**: Why do blood vessels in the heart have thick, elastic walls?  
  - Because the heart is the organ where blood is actually created  
  ✅ Because the blood is under high pressure and flows in only one direction  
  - Because all arteries carry oxygen-rich blood and all veins carry carbon dioxide-rich blood  
  - Because the left and right sides of the heart are connected  
  _Same flaw as Q3: the stem says heart vessels, and B adds an unsupported one-way-flow reason._

**bio_microbes [hybrid] score 2 key OK not sensible H1 H4 H5 H6**: Why do antibiotics work against disease-causing bacteria?  
  - Because the same kind of bacteria helps in making cheese  
  ✅ Because they kill or stop the growth of disease-causing bacteria  
  - Because a bacterium called Lactobacillus multiplies in the milk  
  - Because small that they can be seen only through a microscope  
  _Circular: key restates question; distractors are ungrammatical/irrelevant passage fragments._

**bio_microbes [hybrid_mis] score 2 key OK not sensible H1 H4 H5 H7**: Why do the dough rise and the batter become soft and spongy?  
  - Because carbon dioxide is only a waste product and has no use in nature  
  ✅ Because as yeast respires, it releases carbon dioxide gas  
  - Because oxygen is the only gas that living things need from the air  
  - Because air is made only of oxygen and carbon dioxide  
  _Key copies passage wording; distractors are off-topic generic claims; 'dough rise' grammar off._

**bio_microbes [hybrid] score 2 key OK not sensible H1 H4 H5**: Why do the dough rise and the batter become soft and spongy?  
  - Because many microorganisms are very useful to us  
  ✅ Because as yeast respires, it releases carbon dioxide gas  
  - Because a bacterium called Lactobacillus multiplies in the milk  
  - Because microorganisms are also used to make medicines  
  _Key is only on-topic option; distractors are unrelated passage sentences, not misconceptions._

**bio_microbes [hybrid_mis] score 1 KEY WRONG not sensible H3 H4 H5**: Why is the same kind of bacteria used in making cheese and pickles?  
  - Because the bacteria in curd are 'bad' germs, but we eat them anyway  
  ✅ Because it helps in curd and yeast production  
  - Because microorganisms are also used to make medicines  
  - Because viruses are just a very small type of bacteria  
  _Key mentions yeast/curd, wrong; passage gives no reason; distractors irrelevant._

**bio_microbes [hybrid_mis] score 3 key OK not sensible H4 H5**: Why does curd form in milk?  
  - Because they do not work against viruses  
  ✅ Because a bacterium converts milk into curd  
  - Because pasteurized milk is completely free of all microorganisms  
  - Because the bacteria in curd are 'bad' germs, but we eat them anyway  
  _Correct answer is obvious; distractors off-topic or ungrammatical; key is mostly recall._

**bio_microbes [hybrid] score 1 KEY WRONG not sensible H3 H4 H5**: Why are microorganisms small?  
  - Because other microorganisms break down dead plants  
  ✅ Because they are living things  
  - Because animals into simple substances  
  - Because although some cause diseases  
  _Key doesn't explain smallness; distractors are broken sentence fragments._

**bio_microbes [hybrid_mis] score 2 key OK not sensible H1 H4 H6**: Why do antibiotics work against disease-causing bacteria?  
  - Because the bacteria in curd are 'bad' germs, but we eat them anyway  
  ✅ Because they kill or stop the growth of disease-causing bacteria  
  - Because antibiotics are effective treatments for the common cold and flu  
  - Because viruses are just a very small type of bacteria  
  _Circular key restates question; only one on-topic option besides weak distractors._

**bio_microbes [hybrid] score 2 key OK not sensible H1 H4 H5**: Why does curd form in milk?  
  - Because microorganisms are also used to make medicines  
  ✅ Because a bacterium converts milk into curd  
  - Because other microorganisms break down dead plants  
  - Because they do not work against viruses  
  _Recall; distractors are unrelated passage fragments, key is only fitting option._

**bio_pitcher [hybrid_mis] score 2 key OK SENSIBLE H1 H4 H5 H7**: Why does the pitcher plant still carry out photosynthesis?  
  - Because insectivorous plants eat insects  
  - Because the stem only carries water from the roots to the leaves  
  ✅ Because the insects are not its main source of food but a supplement  
  - Because leaves that are not green do not have chlorophyll and cannot do photosynthesis  
  _Recall of passage sentence; option D is 14 words and far longer than A; weak distractors_

**bio_pitcher [hybrid] score 3 key OK SENSIBLE H1 H4**: Why does the pitcher plant still carry out photosynthesis?  
  - Because the tip of the leaf forms a lid over its mouth  
  - Because the insect drowns in a liquid that contains digestive juices  
  ✅ Because the insects are not its main source of food but a supplement  
  - Because pitcher plants usually grow in soil that is poor in nitrogen  
  _Recall; A and B are irrelevant distractors; D is mildly tempting but wrong_

**bio_pitcher [hybrid_mis] score 1 KEY WRONG not sensible H3 H4 H1**: Why do pitcher plants grow in soil that is poor in nitrogen?  
  - Because sunlight is a material that plants 'eat' to grow  
  - Because plants get their food from the soil through their roots  
  ✅ Because they need nitrogen to make proteins  
  - Because plants can take nitrogen directly from the air through their leaves  
  _Question is illogical; passage gives no reason plants choose poor soil; key doesn't answer it_

**bio_pitcher [hybrid_mis] score 2 key OK not sensible H1 H4 H5 H6**: Why does the pitcher rim attract insects?  
  - Because the insects are not its main source of food  
  - Because insectivorous plants eat insects  
  - Because the insects supply the nitrogen that the soil lacks  
  ✅ Because it produces a sweet substance that attracts insects  
  _Key repeats question words 'attract insects'; distractors off-topic, answer obvious_

**bio_pitcher [hybrid_mis] score 3 key OK SENSIBLE H1 H4**: Why does the insect not climb back out of the pitcher?  
  - Because leaves that are not green do not have chlorophyll and cannot do photosynthesis  
  - Because insectivorous plants eat insects  
  - Because the rim of the pitcher is slippery  
  ✅ Because hair inside the pitcher points downwards  
  _Recall; C is a plausible distractor but A and B are irrelevant_

**bio_pitcher [hybrid] score 2 key OK not sensible H1 H4 H5 H6**: Why does the pitcher rim attract insects?  
  - Because a few plants also trap insects  
  - Because the insects supply the nitrogen that the soil lacks  
  - Because the insects are not its main source of food  
  ✅ Because it produces a sweet substance that attracts insects  
  _Answer leaked by question wording; other options are unrelated passage sentences_

**bio_pitcher [hybrid] score 1 KEY WRONG not sensible H3 H4 H1**: Why do pitcher plants grow in soil that is poor in nitrogen?  
  - Because hair inside the pitcher points downwards  
  - Because a few plants also trap insects  
  ✅ Because they need nitrogen to make proteins  
  - Because the answer lies in the soil  
  _Illogical question; no option answers it; key is a non-sequitur_

**bio_pitcher [hybrid] score 2 key OK SENSIBLE H1 H4**: Why does the insect not climb back out of the pitcher?  
  - Because the answer lies in the soil  
  - Because the rim of the pitcher is slippery  
  - Because a few plants also trap insects  
  ✅ Because hair inside the pitcher points downwards  
  _Recall; A and C are non-answers from unrelated sentences; only B plausible_

**bio_pollination [hybrid_mis] score 3 key OK SENSIBLE H1**: Why is the stamen called the male part of a flower?  
  ✅ Because it produces pollen grains  
  - Because insects visit flowers  
  - Because pollen is the 'seed' of the flower  
  - Because every flower has both male and female parts  
  _Correct, but near-recall; 'male part' answer is stated directly in passage._

**bio_pollination [hybrid] score 1 KEY WRONG not sensible H3 H4 H5**: Why does the male cell join the egg cell?  
  - Because grasses over long distances  
  - Because wind carries the light  
  - Because insects such as bees  
  ✅ Because fertilisation happens  
  _Options are sentence fragments; D is circular. Not a real answer._

**bio_pollination [hybrid] score 3 key OK not sensible H1 H4**: Why do insects like bees and butterflies visit flowers?  
  - Because the ovary grows into a fruit  
  - Because flowers are the reproductive parts of a plant  
  - Because the female part is the pistil  
  ✅ Because they drink nectar from the flowers  
  _Correct, but distractors are irrelevant passage facts; near recall, answerable by form._

**bio_pollination [hybrid_mis] score 1 KEY WRONG not sensible H3 H4**: Why is cross-pollination important for plants?  
  - Because pollen is the 'seed' of the flower  
  ✅ Because it helps plants reproduce with other plants of the same kind  
  - Because insects visit flowers  
  - Because only the petals of a flower are involved in reproduction  
  _Passage never states why cross-pollination matters; B is just its definition._

**bio_pollination [hybrid] score 1 KEY WRONG not sensible H3 H4 H5**: Why is cross-pollination important for plants?  
  - Because the pollen grain grows a tube down to the ovule  
  ✅ Because it helps plants reproduce with other plants of the same kind  
  - Because the male part of a flower is the stamen  
  - Because the new plants do not compete with each other for light  
  _Passage gives no importance of cross-pollination; B restates definition; D is about seeds._

**bio_pollination [hybrid_mis] score 2 key OK not sensible H1 H4 H5 H6**: Why do insects like bees and butterflies visit flowers?  
  ✅ Because they drink nectar from the flowers  
  - Because pollen is the 'seed' of the flower  
  - Because insects visit flowers  
  - Because only the petals of a flower are involved in reproduction  
  _Recall; option C repeats question; B and D are off-topic and obviously wrong._

**bio_pollination [hybrid] score 1 KEY WRONG not sensible H3 H4 H5**: Why do seeds get scattered?  
  - Because the female part is the pistil  
  - Because the ovary grows into a fruit  
  - Because the ovule becomes a seed  
  ✅ Because they are scattered by wind, water  
  _D answers 'how', not why; true reason (avoid competition) is not offered._

**bio_pollination [hybrid_mis] score 1 KEY WRONG not sensible H3 H4 H5**: Why do seeds get scattered?  
  - Because plants grown from vegetative propagation are genetically different from the parent plant  
  ✅ Because they are scattered by wind, water  
  - Because seeds are non-living objects  
  - Because plants can only grow from seeds  
  _B answers how not why; no option gives the competition reason; distractors off-topic._

**bio_respiration [hybrid_mis] score 2 key OK SENSIBLE H1 H4 H5 H6 H7**: Why is respiration hidden during the day?  
  - Because carbon dioxide is only a waste product and has no use in nature  
  ✅ Because photosynthesis uses up more carbon dioxide than respiration releases  
  - Because we inhale pure oxygen and exhale pure carbon dioxide  
  - Because oxygen turns into carbon dioxide inside the lungs  
  _Key copies passage wording; distractors silly/unrelated; question leaks key; B is only fitting option_

**bio_respiration [hybrid] score 1 KEY WRONG not sensible H3 H4 H5 H6**: Why is aerobic respiration called that?  
  - Because through tiny pores in their leaves  
  ✅ Because the glucose is broken down completely into carbon dioxide and water  
  - Because our leg muscles may respire anaerobically  
  - Because respiration is what happens inside the cells of the body  
  _Key explains anaerobic/product, not 'aerobic' (needs oxygen); distractors ungrammatical fragments_

**bio_respiration [hybrid_mis] score 1 KEY WRONG not sensible H3 H4 H5**: Why is aerobic respiration called that?  
  - Because oxygen turns into carbon dioxide inside the lungs  
  ✅ Because the glucose is broken down completely into carbon dioxide and water  
  - Because aerobic respiration is the process of 'making' oxygen for the body  
  - Because we inhale pure oxygen and exhale pure carbon dioxide  
  _Key doesn't explain name (oxygen use); distractors off-topic; keyed answer wrong-ish_

**bio_respiration [hybrid_mis] score 1 KEY WRONG not sensible H3 H4 H6 H5**: Why is it a common mistake to think that plants respire only at night?  
  - Because plants only respire at night and photosynthesize during the day  
  ✅ Because plants respire through their leaves and roots at all times  
  - Because plants get their food from the soil through their roots  
  - Because plants produce oxygen specifically  
  _Passage says it's a mistake because respiration hidden by photosynthesis; B only partly supports_

**bio_respiration [hybrid_mis] score 2 key OK not sensible H1 H4 H5 H6 H7**: Why do leg muscles produce lactic acid during hard exercise?  
  ✅ Because they respire anaerobically and produce lactic acid, causing cramps  
  - Because plants only respire at night when they are not doing photosynthesis  
  - Because lactic acid is produced  
  - Because air entering the lungs causes the chest to expand  
  _Key restates question and passage; distractors off-topic or nonsense; ungrammatical option C_

**bio_respiration [hybrid] score 2 key OK SENSIBLE H1 H4 H5 H6**: Why do leg muscles produce lactic acid during hard exercise?  
  - Because photosynthesis uses up more carbon dioxide than respiration releases  
  ✅ Because they respire anaerobically and produce lactic acid, causing cramps  
  - Because the glucose is broken down completely into carbon dioxide  
  - Because respiration is what happens inside the cells of the body  
  _Key repeats question wording, only on-topic answer; distractors are unrelated passage sentences_

**bio_respiration [hybrid] score 2 key OK SENSIBLE H1 H4 H5 H6**: Why is respiration hidden during the day?  
  - Because respiration is what happens inside the cells of the body  
  ✅ Because photosynthesis uses up more carbon dioxide than respiration releases  
  - Because our leg muscles may respire anaerobically  
  - Because glucose from our food is broken down to release energy  
  _Distractors are true passage sentences not answering why; key copies passage wording_

**bio_respiration [hybrid] score 1 KEY WRONG not sensible H3 H4 H5**: Why does the chest cavity expand when we breathe in?  
  - Because yeast also respires without oxygen  
  ✅ Because air rushes into the lungs  
  - Because our leg muscles may respire anaerobically  
  - Because through tiny pores in their leaves  
  _Premise reversed: air rushing in is effect, not cause; distractors ungrammatical and irrelevant_

**bio_vaccine [hybrid] score 2 key OK not sensible H1 H4 H5**: Why was smallpox feared in the eighteenth century?  
  - Because the body produces antibodies to fight these germs  
  - Because india was declared free of polio in 2014  
  ✅ Because it killed millions and left scars on survivors  
  - Because vaccines have since been made against many diseases  
  _Recall; distractors are unrelated passage fragments, only C is on-topic._

**bio_vaccine [hybrid] score 1 KEY WRONG not sensible H3 H4 H6**: Why did Edward Jenner notice something interesting in the countryside?  
  - Because vaccines have since been made against many diseases  
  ✅ Because he noticed that cowpox was not spreading among milkmaids  
  - Because india was declared free of polio in 2014  
  - Because the body produces antibodies to fight these germs  
  _Key is false: milkmaids with cowpox didn't get smallpox; distractors off-topic._

**bio_vaccine [hybrid] score 2 key OK not sensible H4 H5 H7**: Why do vaccines work?  
  - Because an English doctor named Edward Jenner noticed something interesting in the countryside  
  - Because smallpox was one of the most feared diseases in the world  
  - Because vaccines have since been made against many diseases  
  ✅ Because the body can destroy the germs quickly when they attack later  
  _Distractors are unrelated sentences; A exceeds 12 words; D only on-topic._

**bio_vaccine [hybrid_mis] score 1 KEY WRONG not sensible H3 H4 H6**: Why did Edward Jenner notice something interesting in the countryside?  
  - Because vaccines have since been made against many diseases  
  ✅ Because he noticed that cowpox was not spreading among milkmaids  
  - Because india was declared free of polio in 2014  
  - Because the body produces antibodies to fight these germs  
  _Duplicate of Q4; key contradicts passage._

**bio_vaccine [hybrid_mis] score 2 key OK not sensible H4 H5**: Why do vaccines work?  
  - Because all microorganisms are harmful germs that cause diseases  
  - Because vaccines are dangerous  
  - Because reducing a fever with medicine means the disease is cured  
  ✅ Because the body can destroy the germs quickly when they attack later  
  _Distractors off-topic or silly ('vaccines are dangerous'); D only sensible answer._

**bio_vaccine [hybrid] score 1 KEY WRONG not sensible H3 H4**: Why did James Phipps get slightly ill?  
  - Because india was declared free of polio in 2014  
  - Because an English doctor named Edward Jenner noticed something interesting in the countryside  
  - Because smallpox was one of the most feared diseases in the world  
  ✅ Because he got a small cut from a cowpox sore on his hand  
  _Key wrong: material from milkmaid's sore went into cut on boy's arm._

**bio_vaccine [hybrid_mis] score 2 key OK not sensible H1 H4 H5**: Why was smallpox feared in the eighteenth century?  
  - Because all microorganisms are harmful germs that cause diseases  
  - Because chronic diseases are just acute diseases that haven't been treated yet  
  ✅ Because it killed millions and left scars on survivors  
  - Because mosquitoes and houseflies produce the diseases they carry inside their bodies  
  _Recall; distractors from unrelated topics, C the only on-topic option._

**bio_vaccine [hybrid_mis] score 1 KEY WRONG not sensible H3 H4**: Why did James Phipps get slightly ill?  
  - Because smallpox was one of the most feared diseases in the world  
  - Because viruses are just a very small type of bacteria  
  - Because an English doctor named Edward Jenner noticed something interesting in the countryside  
  ✅ Because he got a small cut from a cowpox sore on his hand  
  _Duplicate of Q8; key misstates the passage, distractors off-topic._

**bio_xylem [hybrid] score 1 key OK not sensible H1 H2 H3 H4 H5 H6 H7**: Why does a plant move water from its roots to leaves?  
  - Because the cross walls between them break down  
  - Because strengthened by a substance called lignin  
  - Because they lose their living contents  
  ✅ Because water travels through xylem  
  _Question is incoherent; options are sentence fragments, only D is on topic, and D leaks 'water'/'xylem'._

**bio_xylem [hybrid] score 2 key OK not sensible H4 H5 H6**: Why are the main cells of xylem dead when they do their job?  
  ✅ Because they lose their living contents and cross walls break down  
  - Because the main force that pulls it is transpiration  
  - Because the water travels through a tissue called xylem  
  - Because carries food made in the leaves to other parts of the plant  
  _Correct option is the longest and the only one that answers; the distractors are unrelated passage fragments, not misconceptions._

**bio_xylem [hybrid_mis] score 3 key OK not sensible H5 H6**: Why are the main cells of xylem dead when they do their job?  
  - Because plants 'suck' water up through the xylem like a person using a straw  
  ✅ Because they lose their living contents and cross walls break down  
  - Because dead cells in a plant are waste products and have no biological function  
  - Because all plant cells have large vacuoles and thick cell walls  
  _Correct option copies passage wording, and 'dead cells' in the question leaks its idea. The distractors are plausible._

**bio_xylem [hybrid_mis] score 2 key OK not sensible H3 H4 H5**: Why is the phloem important in plant growth?  
  ✅ Because it carries food from the leaves to other parts of the plant  
  - Because the stem only carries water from the roots to the leaves  
  - Because phloem only moves food from the leaves down to the roots  
  - Because plants get their food from the soil through their roots  
  _C partly true (phloem moves food, though not only down). The correct option is the only one that copies the passage._

**bio_xylem [hybrid_mis] score 1 key OK not sensible H1 H2 H3 H4 H5**: Why does a plant move water from its roots to leaves?  
  - Because food in plants only moves downwards from the leaves to the roots  
  ✅ Because water travels through xylem  
  - Because roots only hold the plant in the ground  
  - Because the stem only carries water from the roots to the leaves  
  _Question is ungrammatical and unclear; the answer is only 'water travels through xylem', so the other options are off-topic._

**chem_acids [hybrid] score 2 key OK not sensible H1 H4 H5 H6**: Why does blue litmus turn red in an acid?  
  - Because a turmeric stain on a white cloth turns red  
  - Because litmus is a natural indicator obtained from lichens  
  - Because an ant bite injects formic acid into the skin  
  ✅ Because it changes color in an acidic solution  
  _Circular answer; distractors are unrelated passage sentences; D is the only one that fits the question._

**chem_acids [hybrid] score 2 key OK not sensible H1 H4 H5 H6**: Why do we use indicators instead of tasting?  
  - Because turmeric is another natural indicator found in every Indian kitchen  
  ✅ Because tasting is not a safe way to test a substance  
  - Because a turmeric stain on a white cloth turns red  
  - Because an ant bite injects formic acid into the skin  
  _Answer is a copied passage sentence; the other options are off-topic non-reasons._

**chem_acids [hybrid_mis] score 1 KEY WRONG not sensible H3 H4 H1**: Why does a turmeric stain turn red when soap is rubbed on it?  
  ✅ Because it turns yellow when washed with water  
  - Because when phenolphthalein turns colorless, the substance has been destroyed  
  - Because neutralisation results in the total disappearance of the acid and base  
  - Because if litmus paper does not change color, the substance must be water  
  _The real reason (soap is a base) isn't offered. The key doesn't explain the question. B uses phenolphthalein, which is not in the passage._

**chem_acids [hybrid_mis] score 2 KEY WRONG not sensible H1 H4 H5 H6**: Why does blue litmus turn red in an acid?  
  - Because all acids are dangerous and corrosive chemicals  
  ✅ Because it changes color in an acidic solution  
  - Because if litmus paper does not change color, the substance must be water  
  - Because neutralisation results in the total disappearance of the acid and base  
  _Duplicate of Q1; the correct answer is circular and the distractors are irrelevant._

**chem_acids [hybrid_mis] score 2 key OK not sensible H1 H4 H5**: Why do some foods taste sour?  
  - Because all acids are dangerous and corrosive chemicals  
  - Because acids are always liquids  
  - Because neutralisation results in the total disappearance of the acid and base  
  ✅ Because they contain acids  
  _Plain recall; distractors are off-topic or ungrammatical-fit; D is the only fitting option._

**chem_acids [hybrid] score 1 KEY WRONG not sensible H3 H4 H5 H1**: Why do some foods taste sour?  
  - Because reaction is called neutralisation  
  ✅ Because they contain acids  
  - Because curd contains lactic acid  
  - Because vinegar contains acetic acid  
  _C and D also explain sourness, as examples. A is ungrammatical._

**chem_acids [hybrid_mis] score 2 key OK not sensible H1 H4 H5 H6**: Why do we use indicators instead of tasting?  
  - Because if litmus paper does not change color, the substance must be water  
  ✅ Because tasting is not a safe way to test a substance  
  - Because turmeric is another natural indicator found in every Indian kitchen  
  - Because when phenolphthalein turns colorless, the substance has been destroyed  
  _Recall of a sentence; the question leaks 'tasting' and the distractors are weak. D uses phenolphthalein, which is not in the passage._

**chem_changes [hybrid_mis] score 2 key OK SENSIBLE H1 H4**: Why is the reaction of baking soda with vinegar shown as a chemical change?  
  - Because a change in color always proves a new substance has formed  
  ✅ Because bubbles of carbon dioxide gas are produced  
  - Because crystallisation is a chemical change  
  - Because boiling water is a chemical change  
  _Key right, but C and D are silly and off-passage; reads as recall._

**chem_changes [hybrid] score 1 KEY WRONG not sensible H3 H4 H7**: Why is the paper still after cutting it into pieces?  
  - Because no new substance is formed  
  ✅ Because physical changes can be reversed  
  - Because the wax first melts  
  - Because a substance changes its shape  
  _Key wrong: no new substance is the reason, not reversibility. Question is also broken._

**chem_changes [hybrid] score 2 key OK not sensible H1 H4 H5**: Why is the reaction of baking soda with vinegar shown as a chemical change?  
  - Because the souring of milk into curd are all chemical changes  
  - Because some processes involve both kinds of change  
  - Because water can be frozen back into ice  
  ✅ Because bubbles of carbon dioxide gas are produced  
  _Key right, but distractors are ungrammatical, irrelevant passage fragments; D is the only fit._

**chem_changes [hybrid_mis] score 1 KEY WRONG not sensible H3 H4 H7**: Why is the paper still after cutting it into pieces?  
  - Because no new substance is formed  
  ✅ Because physical changes can be reversed  
  - Because the wax first melts  
  - Because a substance changes its shape  
  _Duplicate of Q2: key wrong, A is correct; question wording is broken._

**chem_changes [hybrid] score 2 key OK not sensible H3 H4 H5**: Why is the wax vapour burning in the flame considered a chemical change?  
  - Because shows that a new substance has formed  
  - Because some processes involve both kinds of change  
  ✅ Because it produces carbon dioxide, water vapour, heat  
  - Because water can be frozen back into ice  
  _Option A is ungrammatical, B and D are filler, and the answer list is truncated._

**chem_changes [hybrid_mis] score 3 key OK SENSIBLE H4 H7**: Why is burning paper considered a chemical change?  
  - Because when wood burns, the matter is destroyed and nothing is left but ash  
  ✅ Because new substances are formed, like ash, smoke, and gases  
  - Because boiling water is a chemical change  
  - Because crystallisation is a chemical change  
  _Key right; A has a real misconception but is too long; C and D are silly._

**chem_changes [hybrid] score 2 key OK not sensible H1 H4 H5**: Why is burning paper considered a chemical change?  
  - Because some processes involve both kinds of change  
  - Because changes around us can be grouped into two kinds  
  - Because the souring of milk into curd are all chemical changes  
  ✅ Because new substances are formed, like ash, smoke, and gases  
  _Distractors are irrelevant fragments, one ungrammatical; D is the only answer that fits._

**chem_changes [hybrid_mis] score 4 key OK SENSIBLE **: Why is the wax vapour burning in the flame considered a chemical change?  
  ✅ Because it produces carbon dioxide, water vapour, heat  
  - Because a chemical change only happens if you see an explosion or fire  
  - Because the wick of the candle is what burns to produce the flame  
  - Because boiling water is a chemical change  
  _Key right; B and C are plausible misconceptions; D is weak and A omits light._

**chem_combustion [hybrid_mis] score 3 key OK not sensible H5**: Why is water used on fires?  
  - Because air is the fuel that burns in a fire  
  ✅ Because it cools the burning material and keeps air away  
  - Because water is the best way to put out an electrical fire  
  - Because a substance with a high ignition temperature catches fire very easily  
  _Correct and passage-based; B is the longest and the only option copying passage wording; distractors are weak._

**chem_combustion [hybrid] score 2 key OK not sensible H1 H4 H6**: Why is water not suitable for oil and petrol fires?  
  ✅ Because the oil floats on water and keeps burning  
  - Because a substance reacts with oxygen to give off heat  
  - Because water is the most common extinguisher  
  - Because water should never be used on fires involving electrical equipment  
  _Answer copies passage and leaks via the question; distractors are irrelevant passage sentences._

**chem_combustion [hybrid] score 2 key OK not sensible H1 H4 H6**: Why does kerosene catch fire easily?  
  - Because carbon dioxide is the best extinguisher  
  - Because water is also not suitable for oil  
  ✅ Because it has a low ignition temperature  
  - Because water is the most common extinguisher  
  _Key leaks 'catch fire easily'; distractors are unrelated copied sentences, not misconceptions._

**chem_combustion [hybrid] score 1 key OK not sensible H3 H4 H7**: Why is combustion possible?  
  ✅ Because a fuel, air  
  - Because carbon dioxide is the best extinguisher  
  - Because a substance catches fire  
  - Because the oil floats on water  
  _Key 'a fuel, air' is a truncated fragment; incomplete and ungrammatical; distractors are off-topic._

**chem_combustion [hybrid] score 3 key OK not sensible H5**: Why is water used on fires?  
  - Because water is also not suitable for oil  
  - Because water should never be used on fires involving electrical equipment  
  - Because a substance reacts with oxygen to give off heat  
  ✅ Because it cools the burning material and keeps air away  
  _Correct, but D is the only on-topic and cause-giving option; other options are copied sentences._

**chem_combustion [hybrid_mis] score 2 key OK not sensible H1 H4 H6**: Why is water not suitable for oil and petrol fires?  
  - Because air is the fuel that burns in a fire  
  ✅ Because the oil floats on water and keeps burning  
  - Because metals are non-combustible and can never burn  
  - Because water is the best way to put out an electrical fire  
  _Key leaks via 'oil' and copies passage; distractors are unrelated and implausible._

**chem_combustion [hybrid_mis] score 1 key OK not sensible H3 H4 H7**: Why is combustion possible?  
  - Because a substance with a high ignition temperature catches fire very easily  
  ✅ Because a fuel, air  
  - Because spontaneous combustion happens without any reason or heat  
  - Because air is the fuel that burns in a fire  
  _Key is a truncated fragment 'a fuel, air'; distractor C is silly._

**chem_combustion [hybrid_mis] score 2 key OK not sensible H1 H6 H4**: Why does kerosene catch fire easily?  
  ✅ Because it has a low ignition temperature  
  - Because water is the best way to put out an electrical fire  
  - Because a substance with a high ignition temperature catches fire very easily  
  - Because air is the fuel that burns in a fire  
  _Key leaks 'catch fire easily'; distractors are unrelated or contradict the passage._

**chem_metals [hybrid] score 2 key OK not sensible H1 H4 H5**: Why do solid non-metals break into pieces when hammered?  
  - Because metals are good conductors of heat  
  - Because electric wires are made of copper  
  - Because aluminium foil used to wrap food  
  ✅ Because they are soft and dull  
  _Recall of passage fact; distractors are unrelated fragments, not grammatical 'Because' clauses; only D fits._

**chem_metals [hybrid] score 2 key OK not sensible H4 H5 H6**: Why are cooking vessels made of metal?  
  - Because non-metals form oxides that are acidic in nature  
  ✅ Because metals are good conductors of heat and electricity  
  - Because school bells are made of metal  
  - Because mercury is a metal that is liquid at room temperature  
  _Correct option echoes passage wording and is the only plausible one; distractors are irrelevant facts._

**chem_metals [hybrid_mis] score 1 key OK not sensible H3 H4 H5 H6**: Why do metals form basic oxides?  
  - Because non-metal oxides are always acidic  
  ✅ Because they react with oxygen to form basic oxides  
  - Because non-metals never conduct electricity  
  - Because all metal oxides are basic in nature  
  _Circular: key restates question; D is also true, so arguably two correct._

**chem_metals [hybrid_mis] score 2 key OK not sensible H1 H4 H5**: Why do solid non-metals break into pieces when hammered?  
  ✅ Because they are soft and dull  
  - Because all metals are hard solids that cannot be cut with a knife  
  - Because non-metals never conduct electricity  
  - Because non-metal oxides are always acidic  
  _Duplicate of Q1; distractors off-topic, one invents a claim not in passage; only A fits._

**chem_metals [hybrid_mis] score 2 key OK not sensible H4 H5 H6**: Why is graphite used in the electrodes of cells?  
  ✅ Because it conducts electricity and is a non-metal  
  - Because aluminium foil used to wrap food  
  - Because non-metal oxides are always acidic  
  - Because non-metals never conduct electricity  
  _Key is longest and echoes the question; distractors are irrelevant fragments, one ungrammatical._

**chem_metals [hybrid] score 2 key OK not sensible H4 H5 H6**: Why is graphite used in the electrodes of cells?  
  ✅ Because it conducts electricity and is a non-metal  
  - Because aluminium foil used to wrap food  
  - Because metals form oxides that are basic in nature  
  - Because elements can be broadly divided into metals  
  _Duplicate of Q5; distractors are irrelevant or fragments; key is the only plausible option._

**chem_metals [hybrid_mis] score 2 key OK not sensible H4 H5 H6**: Why are cooking vessels made of metal?  
  - Because all metal oxides are basic in nature  
  ✅ Because metals are good conductors of heat and electricity  
  - Because non-metals never conduct electricity  
  - Because all metals are hard solids that cannot be cut with a knife  
  _Duplicate of Q2; distractors off-topic, and D is a claim not in the passage._

**chem_metals [hybrid] score 1 key OK not sensible H3 H4 H5 H6**: Why do metals form basic oxides?  
  - Because aluminium foil used to wrap food  
  - Because elements can be broadly divided into metals  
  - Because metals are good conductors of heat  
  ✅ Because they react with oxygen to form basic oxides  
  _Circular key restates question; distractors are fragments; not real understanding._

**chem_separation [hybrid_mis] score 2 key OK not sensible H1 H4 H5 H6**: Why is sedimentation used in separating mixtures?  
  ✅ Because it separates solids from liquids, like sand in water  
  - Because heavier solids will always sink to the bottom of a liquid immediately  
  - Because sedimentation only works for mud and water mixtures  
  - Because a sieve can separate a mixture of salt and sand  
  _Key is the only on-topic, correct-looking option; 'always/immediately' distractors; leaks 'sand in water'._

**chem_separation [hybrid] score 1 key OK not sensible H1 H3 H4 H5 H6**: Why is sedimentation used in separating mixtures?  
  ✅ Because it separates solids from liquids, like sand in water  
  - Because the water can be passed through filter paper  
  - Because the salt is left behind as white crystals  
  - Because sea water is let into shallow pits called salt pans  
  _Distractors are unrelated passage facts, not reasons; A leaks the stem's wording._

**chem_separation [hybrid] score 1 KEY WRONG not sensible H3 H4 H5**: Why is handpicking used in villages?  
  - Because the sand can first be allowed to settle at the bottom  
  - Because sea water is let into shallow pits called salt pans  
  ✅ Because the mixture is dropped from a height in the wind  
  - Because a lot of our common salt is obtained from sea water  
  _Key describes winnowing, not handpicking; no option is correct._

**chem_separation [hybrid] score 2 key OK not sensible H1 H3 H4 H5**: Why is the salt left as white crystals?  
  - Because stones are picked out of rice  
  ✅ Because the heat turns the water into vapor  
  - Because husk is separated from grain by winnowing  
  - Because salt is not mined only from the ground  
  _Distractors are off-topic passage sentences; B is the only relevant option, though evaporation is only implied._

**chem_separation [hybrid_mis] score 2 key OK SENSIBLE H3 H4 H5**: Why is the salt left as white crystals?  
  - Because when a salt solution evaporates, the salt also disappears or turns into gas  
  ✅ Because the heat turns the water into vapor  
  - Because filtration can be used to separate dissolved sugar or salt from water  
  - Because evaporation only happens when water is boiling at 100 degrees Celsius  
  _B is the only passage-grounded option; the distractors are obviously wrong, and 'vapor' is used instead of the passage's 'vapour'._

**civ_bill [hybrid] score 2 key OK not sensible H1 H4 H5**: Why is a bill proposed?  
  - Because the bill is passed  
  - Because the bill becomes an Act  
  ✅ Because a new law is needed  
  - Because first the bill is read out  
  _Recall-level; distractors are unrelated passage fragments, not misconceptions; passage never says why bills are proposed._

**civ_bill [hybrid_mis] score 2 key OK not sensible H3 H4 H5**: Why does a bill become an Act?  
  - Because a bill passed by both Houses of Parliament becomes a law automatically  
  ✅ Because the President signs it and gives assent  
  - Because the President is not a part of Parliament  
  - Because a bill becomes a law  
  _Option A also plausible (passed by both Houses then assent); D circular; C silly; longest-option giveaway._

**civ_bill [hybrid_mis] score 2 key OK not sensible H3 H4 H5**: Why can a money bill be introduced only in Lok Sabha?  
  ✅ Because it deals with taxes and government spending  
  - Because a bill is voted on immediately after it is introduced, without any discussion  
  - Because the Rajya Sabha can reject a Money Bill passed by the Lok Sabha  
  - Because citizens vote directly to choose the members of the Rajya Sabha  
  _Passage doesn't give this reason; A copies passage wording, others are obviously wrong._

**civ_bill [hybrid] score 1 KEY WRONG not sensible H3 H4 H5**: Why is a bill often sent to a committee?  
  - Because a proposal for a new law is called a bill  
  ✅ Because it is debated and members may suggest changes  
  - Because once both Houses have passed a bill  
  - Because the House then discusses each part of the bill  
  _Key B describes debate, not committee reason; options are ungrammatical sentence fragments._

**civ_bill [hybrid] score 1 KEY WRONG not sensible H3 H4 H5**: Why can a money bill be introduced only in Lok Sabha?  
  - Because the House then discusses each part of the bill  
  ✅ Because it deals with taxes and government spending  
  - Because once both Houses have passed a bill  
  - Because first the bill is read out  
  _Passage gives no reason for Lok Sabha only; B is a definition; distractors are fragments._

**civ_bill [hybrid_mis] score 1 KEY WRONG not sensible H3 H4 H5**: Why is a bill often sent to a committee?  
  - Because a bill is voted on immediately after it is introduced, without any discussion  
  ✅ Because it is debated and members may suggest changes  
  - Because a bill becomes a law  
  - Because a bill passed by both Houses of Parliament becomes a law automatically  
  _Key B concerns debate, not committee; other options irrelevant or false; no proven reason._

**civ_bill [hybrid] score 2 key OK not sensible H4 H5**: Why does a bill become an Act?  
  - Because once both Houses have passed a bill  
  ✅ Because the President signs it and gives assent  
  - Because first the bill is read out  
  - Because the House then discusses each part of the bill  
  _B is the only complete clause; distractors are ungrammatical fragments, form gives answer away._

**civ_panchayat [hybrid] score 2 KEY WRONG not sensible H3 H5 H6**: Why can the villagers question the sarpanch?  
  ✅ Because they can suggest new work and ask about money usage at meetings  
  - Because the Gram Sabha plays an important role in keeping the panchayat honest  
  - Because local matters are managed by an elected body called the Gram Panchayat  
  - Because one third of the seats in panchayats are reserved for women  
  _A restates the question; B is the passage's stated reason. Circular, two defensible answers._

**civ_panchayat [hybrid] score 2 key OK not sensible H4 H5 H6**: Why is the secretary of the Gram Panchayat not elected?  
  - Because keeps a record of what is discussed  
  ✅ Because the government appoints him, not by election  
  - Because every adult who lives in the village  
  - Because many states have raised this to half  
  _Fragment distractors off-topic; key repeats 'not elected'; only grammatical option._

**civ_panchayat [hybrid_mis] score 2 key OK SENSIBLE H3 H4 H5**: Why is the Panchayat Samiti formed?  
  - Because the Gram Sabha consists only of the elected members of the Panchayat  
  ✅ Because it is formed at the block level  
  - Because the Zila Parishad makes laws for the whole country  
  - Because the Gram Panchayat only handles village festivals and has no real responsibilities  
  _Silly distractors; 'block level' is location, not a reason._

**civ_panchayat [hybrid_mis] score 2 key OK SENSIBLE H1 H5 H6**: Why can the villagers question the sarpanch?  
  ✅ Because they can suggest new work and ask about money usage at meetings  
  - Because panchayat funds come only from the pocket money of the Sarpanch and members  
  - Because the Sarpanch is appointed by the district collector and not chosen by villagers  
  - Because the Sarpanch has absolute power to make all village decisions alone  
  _Key restates question, longest option; distractors contradict passage obviously._

**civ_panchayat [hybrid_mis] score 3 key OK SENSIBLE H6 H5**: Why is the secretary of the Gram Panchayat not elected?  
  - Because ward councillors are appointed by the government, not elected  
  ✅ Because the government appoints him, not by election  
  - Because the Gram Panchayat only handles village festivals and has no real responsibilities  
  - Because the Gram Sabha consists only of the elected members of the Panchayat  
  _Key repeats the question wording; only one copying passage; gendered 'him'._

**civ_rights [hybrid_mis] score 2 key OK not sensible H1 H4 H5**: Why is the Cultural and Educational Rights important?  
  - Because fundamental Rights mean I can do whatever I want at any time  
  ✅ Because it allows minorities to preserve their culture and education  
  - Because right to Equality means everyone must be treated exactly the same  
  - Because only the Supreme Court can be approached when a Fundamental Right is violated  
  _Near-recall; distractors off-topic or silly, B only on-topic option._

**civ_rights [hybrid_mis] score 2 key OK not sensible H4 H5**: Why is the right to constitutional remedies important?  
  - Because only ordinary citizens need to follow the Constitution  
  ✅ Because it ensures citizens can seek justice when their rights are violated  
  - Because fundamental Rights mean I can do whatever I want at any time  
  - Because only the Supreme Court can be approached when a Fundamental Right is violated  
  _Distractors silly or off-topic; B is the only fitting option._

**civ_rights [hybrid] score 2 key OK not sensible H4 H5 H1**: Why is the Cultural and Educational Rights important?  
  - Because without it all the other rights would have no value  
  - Because the Constitution of India gives every citizen certain basic rights  
  - Because the employment of children below 14 years in factories  
  ✅ Because it allows minorities to preserve their culture and education  
  _C is ungrammatical, A and B belong to other rights; D stands out._

**civ_rights [hybrid] score 2 key OK not sensible H1 H4 H5**: Why is freedom of speech included in the Right to Freedom?  
  - Because everyone has equal access to public places such as parks  
  ✅ Because it allows people to express themselves freely  
  - Because the Right against Exploitation forbids human trafficking  
  - Because the employment of children below 14 years in factories  
  _Distractors are unrelated fragments; B is the only on-topic option._

**civ_rights [hybrid_mis] score 2 key OK not sensible H3 H4 H5**: Why is equality important in the text?  
  - Because article 15 bans discrimination only on the basis of caste  
  ✅ Because equality is the foundation of justice and fairness in society  
  - Because right to Equality means everyone must be treated exactly the same  
  - Because only the Supreme Court can be approached when a Fundamental Right is violated  
  _Key's 'foundation of justice' is not in the passage; distractors weak._

**civ_rights [hybrid_mis] score 2 key OK not sensible H1 H4 H5**: Why is freedom of speech included in the Right to Freedom?  
  ✅ Because it allows people to express themselves freely  
  - Because only the Supreme Court can be approached when a Fundamental Right is violated  
  - Because freedom of speech allows me to say anything I want, including inciting violence  
  - Because fundamental Rights mean I can do whatever I want at any time  
  _Only C is a real misconception; B and D are off-topic._

**civ_rights [hybrid] score 2 key OK not sensible H4 H5**: Why is the right to constitutional remedies important?  
  - Because no one can be discriminated against on the basis of religion  
  - Because the Constitution of India gives every citizen certain basic rights  
  ✅ Because it ensures citizens can seek justice when their rights are violated  
  - Because everyone has equal access to public places such as parks  
  _Three distractors are other rights' facts; C is the only on-topic option._

**civ_rights [hybrid] score 2 KEY WRONG not sensible H3 H4**: Why is equality important in the text?  
  - Because without it all the other rights would have no value  
  ✅ Because equality is the foundation of justice and fairness in society  
  - Because everyone has equal access to public places such as parks  
  - Because the Constitution of India gives every citizen certain basic rights  
  _B is unsupported by the passage; C is passage-backed equality content._

**civ_secularism [hybrid_mis] score 2 key OK not sensible H3 H4 H5 H6 H7**: Why is the celebration of a religious festival not allowed in government schools?  
  - Because the government should never interfere in religious matters, even if they are harmful  
  ✅ Because students are free to celebrate at home, not in school  
  - Because if the government gives money to a religious school, it is not secular  
  - Because secularism means the government is against religion or is atheist  
  _B restates home-celebration; the passage's real reason (no State-imposed religion) is absent; options off-topic or leak._

**civ_secularism [hybrid] score 2 key OK not sensible H1 H2 H4 H5 H6**: Why is the law not requiring people riding two-wheelers to wear helmets?  
  - Because even though some people defended it as part of their religious tradition  
  - Because the State does not force any religion on people  
  - Because members of the same religion do not dominate each other  
  ✅ Because Sikhs who wear turbans are allowed to not wear helmets  
  _Garbled stem; D copies passage and leaks 'helmet'; distractors are unrelated sentence fragments._

**civ_secularism [hybrid_mis] score 2 key OK not sensible H1 H2 H4 H5 H6**: Why is the law not requiring people riding two-wheelers to wear helmets?  
  - Because even though some people defended it as part of their religious tradition  
  ✅ Because Sikhs who wear turbans are allowed to not wear helmets  
  - Because members of the same religion do not dominate each other  
  - Because the State does not force any religion on people  
  _Stem is garbled, and it leaks the answer; distractors are loose passage fragments._

**eco_money [hybrid] score 2 key OK SENSIBLE H1 H4 H5 H6**: Why is money called a medium of exchange?  
  - Because people exchanged goods directly for other goods  
  ✅ Because money acts as a go-between in exchanges  
  - Because the law makes it the official currency  
  - Because people also keep money in banks as deposits  
  _Key right, but it's recall; distractors are copied passage fragments, and the stem leaks 'exchange'._

**eco_money [hybrid] score 2 key OK SENSIBLE H1 H4 H5 H6**: Why is money used as a medium of exchange?  
  - Because people exchanged goods directly for other goods  
  ✅ Because it acts as a go-between in exchanges  
  - Because many things have been used as money  
  - Because people also keep money in banks as deposits  
  _Recall of passage phrase; distractors are passage fragments, not misconceptions._

**eco_money [hybrid_mis] score 2 key OK SENSIBLE H1 H3 H4 H5**: Why did people use the barter system?  
  - Because money is valuable only  
  ✅ Because they exchanged goods directly for other goods  
  - Because modern paper money has intrinsic value like gold or silver  
  - Because barter is efficient if you have enough goods to trade  
  _Circular key; distractors are invented outside-passage or fragmentary, B alone copies passage._

**eco_money [hybrid_mis] score 2 key OK SENSIBLE H1 H4 H5 H6**: Why is money called a medium of exchange?  
  - Because any currency note or coin can be legally refused by a seller  
  ✅ Because money acts as a go-between in exchanges  
  - Because modern paper money has intrinsic value like gold or silver  
  - Because money is valuable only  
  _Recall; only B copies passage wording, distractors are invented and weak._

**eco_money [hybrid_mis] score 2 key OK SENSIBLE H1 H4 H5 H6**: Why is money used as a medium of exchange?  
  ✅ Because it acts as a go-between in exchanges  
  - Because modern paper money has intrinsic value like gold or silver  
  - Because money is valuable only  
  - Because the bank keeps all deposited money in its vault until depositors withdraw it  
  _Recall of the definition; B and C are off-passage and weak, A copies wording._

**eco_shg [hybrid_mis] score 2 key OK not sensible H4 H5 H6**: Why did the bank lend money to the group?  
  - Because the bank keeps all deposited money in its vault until depositors withdraw it  
  ✅ Because the members were responsible for repaying  
  - Because money is valuable only  
  - Because collateral is a fee paid to the bank for taking a loan  
  _Key correct but near-recall; distractors A, C, D are off-topic/absurd, B is the only passage-based option._

**eco_shg [hybrid] score 2 key OK not sensible H3 H4 H5**: Why do members get loans from the group?  
  - Because the group becomes eligible for a loan from a bank  
  - Because the bank lends to the group as a whole  
  - Because a typical SHG has 15 to 20 members  
  ✅ Because the group decides the purpose, amount, and repayment schedule  
  _Distractors are passage facts, not misconceptions; D is longest, and the 'Because' stems fit poorly._

**eco_shg [hybrid_mis] score 2 key OK not sensible H4 H5**: Why do members get loans from the group?  
  ✅ Because the group decides the purpose, amount, and repayment schedule  
  - Because collateral is a fee paid to the bank for taking a loan  
  - Because the RBI directly gives loans to small farmers and businesses  
  - Because interest on a deposit and interest on a loan are the same rate  
  _Distractors B, C, D are off-topic or silly; A is the only passage-based option._

**eco_shg [hybrid] score 1 KEY WRONG not sensible H3 H4 H5**: Why do banks ask for collateral?  
  - Because the group becomes eligible for a loan from a bank  
  - Because members can take small loans from the group to meet their needs  
  - Because the interest charged is far lower than that of a moneylender  
  ✅ Because they want to lend money to poor people who can't repay it  
  _Key D is not supported; passage says collateral protects banks. Distractors are mismatched passage facts._

**eco_shg [hybrid] score 1 key OK not sensible H3 H4 H5**: Why did the bank lend money to the group?  
  - Because perhaps fifty or a hundred rupees  
  - Because the group decides the purpose  
  ✅ Because the members were responsible for repaying  
  - Because they are forced to borrow from moneylenders  
  _Key C is correct, but A is a fragment and B and D are nonsense or off-topic._

**eco_shg [hybrid_mis] score 1 KEY WRONG not sensible H3 H4 H5**: Why do banks ask for collateral?  
  - Because the RBI directly gives loans to small farmers and businesses  
  ✅ Because they want to lend money to poor people who can't repay it  
  - Because collateral is a fee paid to the bank for taking a loan  
  - Because interest on a deposit and interest on a loan are the same rate  
  _Key B is wrong; passage says collateral is sold if the loan isn't repaid. Distractors are off-topic._

**eco_unemployment [hybrid] score 1 KEY WRONG not sensible H3 H4 H5 H6 H7**: Why does seasonal unemployment affect people in the harvest season?  
  - Because the amount of grain produced would stay the same  
  ✅ Because they work for four months and have no job during the harvest  
  - Because unemployment wastes a country's human resource  
  - Because promises 100 days of paid work in a year to rural households  
  _B contradicts passage (idle four months after harvest); all options ungrammatical fragments, no correct answer._

**eco_unemployment [hybrid] score 2 key OK not sensible H4 H5 H6**: Why is this type of unemployment common in Indian agriculture?  
  - Because unemployment wastes a country's human resource  
  - Because has no work for four months  
  ✅ Because many families share small pieces of land  
  - Because economists call this disguised unemployment  
  _Key right, but distractors are copied passage fragments; B ungrammatical; question vague about 'this type'._

**eco_unemployment [hybrid_mis] score 2 key OK not sensible H2 H3 H4 H5**: Why is this type of unemployment common in Indian agriculture?  
  - Because disguised unemployment means people are hiding from work  
  ✅ Because many families share small pieces of land  
  - Because all farmers in India own the land they cultivate  
  - Because seasonal unemployment happens only in farming  
  _'This type' ambiguous; seasonal also plausibly fits; key is only passage-copied option; D/A weak._

**eco_unemployment [hybrid] score 2 key OK not sensible H1 H3 H4 H5**: Why is farming in many areas important?  
  ✅ Because it depends on the rain and provides work during sowing and harvesting  
  - Because five members of the family work on it  
  - Because promises 100 days of paid work in a year to rural households  
  - Because the amount of grain produced would stay the same  
  _Vague question; A is longest and only fitting option; others are ungrammatical off-topic fragments._

**eco_unemployment [hybrid_mis] score 1 KEY WRONG not sensible H3 H5**: Why does seasonal unemployment affect people in the harvest season?  
  ✅ Because they work for four months and have no job during the harvest  
  - Because seasonal unemployment happens only in farming  
  - Because farming work is the same amount in every month  
  - Because disguised unemployment means people are hiding from work  
  _Key A is false: seasonal unemployment occurs between seasons, not during harvest; question premise wrong._

**eco_unemployment [hybrid_mis] score 2 key OK not sensible H1 H3 H4 H5**: Why is farming in many areas important?  
  - Because farm work is only done by men  
  ✅ Because it depends on the rain and provides work during sowing and harvesting  
  - Because farming work is the same amount in every month  
  - Because everyone in a village works in farming  
  _Vague 'important' question; B longest, only on-topic option; distractors silly and off-passage._

**env_solar [hybrid] score 4 key OK SENSIBLE **: Why are many cells joined together in a panel?  
  - Because spread over about 56 square kilometres  
  ✅ Because a single cell only produces half a volt  
  - Because solar energy does not produce smoke or harmful gases  
  - Because solar panels produce no electricity at night  
  _Clear cause-effect; option A is odd and 'Because' fragments are awkward._

**env_solar [hybrid_mis] score 3 key OK not sensible H4**: Why are many cells joined together in a panel?  
  ✅ Because a single cell only produces half a volt  
  - Because solar panels give no power on cloudy days  
  - Because solar panels need hot weather and give no electricity in cool weather  
  - Because the International Solar Alliance is a company that sells solar panels  
  _Correct, but D (International Solar Alliance) is off-passage and silly; C is weak._

**env_solar [hybrid_mis] score 2 key OK not sensible H1 H5 H6**: Why is solar energy used in the production of electricity?  
  - Because solar energy is renewable  
  ✅ Because solar panels convert solar energy directly into electricity  
  - Because solar panels need hot weather and give no electricity in cool weather  
  - Because solar panels give no power on cloudy days  
  _Key restates the passage and leaks 'solar energy/electricity'; it is the only option copying passage wording._

**env_solar [hybrid] score 1 KEY WRONG not sensible H3 H5**: Why is solar energy used in the production of electricity?  
  - Because many cells are joined together in a panel  
  ✅ Because solar panels convert solar energy directly into electricity  
  - Because a solar panel is made of many solar cells  
  - Because solar energy does not produce smoke or harmful gases  
  _B, C and D are all passage-true; the key is arguable and ambiguous._

**env_solar [hybrid_mis] score 1 KEY WRONG not sensible H3 H4 H6**: Why is solar energy efficient at night?  
  - Because solar panels need hot weather and give no electricity in cool weather  
  ✅ Because it produces no electricity at night and less on cloudy days  
  - Because solar energy is renewable  
  - Because solar panels give no power on cloudy days  
  _False premise: solar is not efficient at night; the key contradicts the question._

**env_solar [hybrid] score 1 KEY WRONG not sensible H3 H4**: Why is solar energy efficient at night?  
  - Because solar energy does not produce smoke or harmful gases  
  - Because the Sun is the main source of energy for the Earth  
  - Because a solar panel is made of many solar cells  
  ✅ Because it produces no electricity at night and less on cloudy days  
  _False premise: solar is not efficient at night; every option is wrong or irrelevant._

**env_waste [hybrid_mis] score 2 key OK not sensible H1 H4 H5**: Why do the waste end up in the dustbin?  
  - Because only sea animals are harmed by plastic  
  ✅ Because they are thrown away every day  
  - Because plastic takes only a few years to disappear in nature, like paper  
  - Because burning plastic makes it biodegradable  
  _Circular answer; distractors are silly and unrelated to why waste goes in dustbin._

**env_waste [hybrid_mis] score 2 key OK not sensible H1 H4 H6**: Why is kitchen waste called biodegradable waste?  
  ✅ Because tiny organisms in the soil can break it down  
  - Because microplastics are tiny living organisms that grow in plastic  
  - Because when plastic breaks into tiny pieces, it has disappeared from the environment  
  - Because burning plastic makes it biodegradable  
  _Plain recall; distractors off-topic plastic claims; question leaks answer._

**env_waste [hybrid_mis] score 2 key OK not sensible H3 H4 H5**: Why do landfills become huge and smelly?  
  - Because taken to low-lying open areas called landfills  
  - Because waste can be turned into compost  
  - Because every household throws away some waste  
  ✅ Because waste is not separated at home  
  _Cause only implied by passage; option A is a fragment; weak distractors._

**env_waste [hybrid] score 2 key OK not sensible H3 H4 H5**: Why do landfills become huge and smelly?  
  - Because taken to low-lying open areas called landfills  
  ✅ Because waste is not separated at home  
  - Because refuse what you do not need  
  - Because leftover food is called biodegradable waste  
  _Cause only implied; C and A are ungrammatical fragments; distractors irrelevant._

**env_waste [hybrid_mis] score 1 KEY WRONG not sensible H3 H4 H5**: Why is reducing plastic use important?  
  - Because burning plastic is a good way to get rid of it  
  ✅ Because it helps reduce harmful gases and improves food security  
  - Because only sea animals are harmed by plastic  
  - Because if plastic can be recycled, it is fine to use  
  _'Improves food security' is not in the passage; key is unsupported._

**env_waste [hybrid] score 2 key OK not sensible H3 H4 H5 H6**: Why is vermicomposting used?  
  - Because tiny organisms in the soil can break it down  
  - Because broken toys all end up in the dustbin  
  - Because taken to low-lying open areas called landfills  
  ✅ Because it makes the process faster and is called vermicomposting  
  _Correct option repeats the question's word and is longest; distractors are fragments._

**env_waste [hybrid] score 2 key OK not sensible H1 H4 H5**: Why is kitchen waste called biodegradable waste?  
  - Because the waste is collected by municipal workers  
  ✅ Because tiny organisms in the soil can break it down  
  - Because broken toys all end up in the dustbin  
  - Because every household throws away some waste  
  _Recall; the three distractors are unrelated passage snippets, not misconceptions._

**env_waste [hybrid] score 1 KEY WRONG not sensible H3 H4 H5**: Why is reducing plastic use important?  
  ✅ Because it helps reduce harmful gases and improves food security  
  - Because plastic bags are a special problem  
  - Because broken toys all end up in the dustbin  
  - Because tiny organisms in the soil can break it down  
  _Key claims food security, unsupported; distractors are irrelevant fragments._

**geo_ghats [hybrid_mis] score 2 key OK not sensible H2 H4 H6 H3**: Why are the examples given in the text included?  
  - Because blooms only once in twelve years  
  ✅ Because they are examples of endemic species  
  - Because scientists call such places biodiversity hotspots  
  - Because they are older than the Himalayas  
  _Vague 'the examples' with no referent; options A/D irrelevant, so answer guessable._

**geo_ghats [hybrid] score 2 key OK not sensible H2 H4 H6 H3**: Why are the examples given in the text included?  
  - Because blooms only once in twelve years  
  ✅ Because they are examples of endemic species  
  - Because scientists call such places biodiversity hotspots  
  - Because they are older than the Himalayas  
  _Exact duplicate of Q1; vague question, weak distractors, 'endemic' leaks._

**geo_ghats [hybrid_mis] score 3 key OK SENSIBLE H5 H4**: Why do the Western Ghats support thick evergreen forests?  
  - Because rain shadow areas receive no rain at all  
  ✅ Because they receive heavy rain from the monsoon  
  - Because tropical evergreen forests are found only in India's Western Ghats  
  - Because tropical evergreen forests have only a few kinds of trees, like a plantation  
  _Correct, but C and D are longer; distractors off-passage, B shortest and passage-copied._

**geo_ghats [hybrid] score 2 key OK not sensible H4 H5 H1**: Why do the Western Ghats support thick evergreen forests?  
  - Because uNESCO declared the Western Ghats a World Heritage Site in 2012  
  - Because these forests are under threat from mining  
  - Because many of the species living there are endemic  
  ✅ Because they receive heavy rain from the monsoon  
  _Distractors are unrelated passage facts, not misconceptions; D copies passage wording; recall._

**geo_ghats [hybrid] score 2 key OK not sensible H3 H4 H5**: Why are the Western Ghats important?  
  - Because the Western Ghats receive heavy rain from the south-west monsoon  
  ✅ Because they supply water to millions of people in southern India  
  - Because uNESCO declared the Western Ghats a World Heritage Site in 2012  
  - Because supports thick evergreen forests on their western slopes  
  _Vague 'important'; A and C also plausible; D ungrammatical; copy-paste distractors._

**geo_ghats [hybrid_mis] score 2 key OK not sensible H4 H5 H3**: Why are the Western Ghats important?  
  - Because tropical evergreen forests are found only in India's Western Ghats  
  ✅ Because they supply water to millions of people in southern India  
  - Because jet streams are strong winds that blow near the ground over India  
  - Because the monsoon arrives in all parts of India on the same date  
  _Distractors off-topic (jet streams, monsoon); B only on-topic option; vague 'important'._

**geo_groundwater [hybrid] score 2 key OK not sensible H3 H4 H5**: Why do people think groundwater flows in underground rivers or lakes?  
  - Because groundwater fills the tiny spaces between grains of sand  
  - Because some of the water soaks into the ground  
  ✅ Because they imagine it, but it's mostly not true  
  - Because the water table has dropped by many metres  
  _Key is circular and unhelpful; the passage doesn't say why people believe it; distractors are random passage facts._

**geo_groundwater [hybrid_mis] score 1 key OK not sensible H3 H4 H5**: Why do people think groundwater flows in underground rivers or lakes?  
  - Because rivers and lakes hold most of the fresh water on Earth  
  ✅ Because they imagine it, but it's mostly not true  
  - Because groundwater is stored in large empty underground swimming pools or rivers  
  - Because harvested rainwater is useful only for storing in tanks, not for refilling groundwater  
  _Key restates 'imagine it'; C is a silly option; D is off-topic, so B stands out._

**geo_groundwater [hybrid_mis] score 4 key OK SENSIBLE **: Why is water table dropping in many parts of India?  
  ✅ Because water is pumped out faster than it can be replenished by rainfall  
  - Because every part of India gets about the same amount of rain  
  - Because all the rain that falls on the ground becomes drinking water  
  - Because the water table is a fixed level that never changes  
  _Sound cause question; distractors are plausible misconceptions; A is longest but a minor issue._

**geo_groundwater [hybrid] score 2 key OK not sensible H3 H4 H5**: Why is infiltration important?  
  - Because the water table is not fixed  
  ✅ Because it helps water reach the ground  
  - Because process is called infiltration  
  - Because much like water fills a sponge  
  _Key is vague; C and D are sentence fragments from the passage, not real options._

**geo_groundwater [hybrid_mis] score 2 key OK not sensible H3 H4 H6**: Why do we find water in the ground when we dig a well?  
  - Because the water table is a fixed level that never changes  
  ✅ Because groundwater is found at some depth below the ground  
  - Because soil is solid and does not allow water to pass through it  
  - Because all the rain that falls on the ground becomes drinking water  
  _Key just restates the question; passage does not support it as a reason. Other options are off-topic._

**geo_groundwater [hybrid_mis] score 2 key OK not sensible H3 H4 H5**: Why is infiltration important?  
  - Because the water table is a fixed level that never changes  
  ✅ Because it helps water reach the ground  
  - Because soil is solid and does not allow water to pass through it  
  - Because all the rain that falls on the ground becomes drinking water  
  _Key is vague; the distractors are off-topic, so B is the only fit by form._

**geo_monsoon [hybrid] score 2 key OK not sensible H1 H4 H5 H6**: Why do winds blow from high pressure to low pressure?  
  - Because the direction of the winds reverses with the seasons  
  ✅ Because of the pressure difference, winds move from high pressure to low pressure  
  - Because an area of low pressure forms over the plains of north-western India  
  - Because mawsynram in Meghalaya receives one of the highest rainfalls in the world  
  _Key restates the question; circular. Option D is off-topic. Passage gives no reason._

**geo_monsoon [hybrid_mis] score 3 key OK SENSIBLE H1 H4 H5**: Why does the eastern side of India receive less rain?  
  - Because winds blow from low pressure areas to high pressure areas  
  ✅ Because it lies in the rain shadow  
  - Because rain shadow areas receive no rain at all  
  - Because jet streams are strong winds that blow near the ground over India  
  _Near recall of 'rain shadow'. Jet-stream distractor is implausible; B alone copies passage._

**geo_monsoon [hybrid] score 2 key OK SENSIBLE H1 H4 H5 H7**: Why is the word monsoon called a monsoon climate?  
  - Because the air over the Indian Ocean is cooler  
  ✅ Because the direction of the winds reverses with the seasons  
  - Because the land heats up much faster than the sea  
  - Because india's climate is called a monsoon climate  
  _Awkward question wording; distractors are passage sentences, and D is circular. Mostly recall._

**geo_monsoon [hybrid_mis] score 3 key OK SENSIBLE H1 H4 H7**: Why is the word monsoon called a monsoon climate?  
  - Because india's climate is called a monsoon climate  
  ✅ Because the direction of the winds reverses with the seasons  
  - Because climate is just the weather of a single day  
  - Because the monsoon arrives in all parts of India on the same date  
  _Awkward wording and recall; option A circular, but C and D are real misconceptions._

**geo_monsoon [hybrid] score 2 key OK not sensible H1 H4 H6**: Why do the monsoon winds change direction in October and November?  
  - Because the direction of the winds reverses with the seasons  
  - Because india's climate is called a monsoon climate  
  ✅ Because the land cools and the winds reverse  
  - Because the eastern side receives much less rain  
  _Question leaks 'reverse'; B and D are irrelevant, so C is the only fit._

**geo_monsoon [hybrid] score 2 key OK not sensible H1 H4 H5**: Why does the eastern side of India receive less rain?  
  - Because the eastern side receives much less rain  
  ✅ Because it lies in the rain shadow  
  - Because india's climate is called a monsoon climate  
  - Because the pressure there is higher  
  _A and C are circular or irrelevant; B is the only plausible, passage-worded option._

**geo_monsoon [hybrid_mis] score 2 key OK SENSIBLE H1 H4 H5 H6**: Why do winds blow from high pressure to low pressure?  
  - Because winds blow from low pressure areas to high pressure areas  
  ✅ Because of the pressure difference, winds move from high pressure to low pressure  
  - Because jet streams are strong winds that blow near the ground over India  
  - Because the Coriolis force is what makes air move from high to low pressure  
  _Tautological key; Coriolis needs outside knowledge. A is the reversed misconception._

**geo_monsoon [hybrid_mis] score 2 key OK not sensible H1 H4 H6**: Why do the monsoon winds change direction in October and November?  
  ✅ Because the land cools and the winds reverse  
  - Because the monsoon arrives in all parts of India on the same date  
  - Because rain shadow areas receive no rain at all  
  - Because winds blow from low pressure areas to high pressure areas  
  _Question leaks 'winds reverse'; B and C are irrelevant, so A is the only fit._

**geo_seasons [hybrid] score 2 key OK SENSIBLE H1 H6**: Why is the Earth called the planet of revolution?  
  - Because the Northern Hemisphere leans towards the Sun for part of the year  
  - Because the half of the Earth facing the Sun has day  
  - Because the Earth is closest to the Sun in early January  
  ✅ Because it travels around the Sun in a path called its orbit  
  _Pure recall; 'revolution' and 'orbit' wording matches passage; 'planet of revolution' is odd phrasing._

**geo_seasons [hybrid_mis] score 2 key OK SENSIBLE H1 H6**: Why is the Earth called the planet of revolution?  
  - Because a leap year has 365 days and an extra day is dropped  
  ✅ Because it travels around the Sun in a path called its orbit  
  - Because the Earth takes 24 hours to go around the Sun once  
  - Because the Sun moves around the Earth every day  
  _Same recall question as Q1, duplicated; the correct option copies passage wording._

**geo_soils [hybrid_mis] score 1 KEY WRONG not sensible H1 H3 H4 H5 H6**: Why do red and yellow soils form on old crystalline rocks?  
  ✅ Because they get their red color from iron  
  - Because soil is formed only from the weathering of rocks  
  - Because arid soil is red or yellow in colour and very rich in humus  
  - Because laterite soil is fertile and good for most crops  
  _Passage gives iron as reason for colour, not formation; A leaks 'red' and is only on-topic option._

**geo_soils [hybrid_mis] score 1 KEY WRONG not sensible H3 H4 H7**: Why is soil important in India?  
  - Because soil formation is a quick process that takes only a few years  
  ✅ Because it provides food and sustains the environment over thousands of years  
  - Because soil is formed only from the weathering of rocks  
  - Because laterite soil is fertile and good for most crops  
  _Key B invents 'sustains environment'; passage says food grows in it; B is longest._

**geo_soils [hybrid] score 1 KEY WRONG not sensible H3 H4 H5 H7**: Why is soil important in India?  
  - Because india has many types of soil  
  ✅ Because it provides food and sustains the environment over thousands of years  
  - Because laterite soil forms in areas with high temperature  
  - Because soil is a very important resource  
  _Key B invents content; D is nearest to passage but is circular restatement._

**geo_soils [hybrid_mis] score 1 KEY WRONG not sensible H3 H4 H6**: Why is black soil called regur soil?  
  - Because black soil is best for growing rice and jute  
  ✅ Because it is found in the Deccan plateau, in Maharashtra, Gujarat  
  - Because laterite soil is fertile and good for most crops  
  - Because alluvial soil is only found in the Northern Plains  
  _Passage gives no reason for the regur name; B is location, not cause._

**geo_soils [hybrid] score 1 KEY WRONG not sensible H3 H4 H5**: Why do red and yellow soils form on old crystalline rocks?  
  - Because rocks are slowly broken down by changes in temperature  
  ✅ Because they get their red color from iron  
  - Because almost all our food grows in it  
  - Because alluvial soil is the most widespread  
  _Iron explains colour, not formation; A is closest to a formation answer. Key doubtful._

**geo_soils [hybrid] score 1 KEY WRONG not sensible H3 H4**: Why is black soil called regur soil?  
  - Because yellow soils develop on old crystalline rocks in the eastern  
  - Because laterite soil forms in areas with high temperature  
  ✅ Because it is found in the Deccan plateau, in Maharashtra, Gujarat  
  - Because rocks are slowly broken down by changes in temperature  
  _Location does not explain the name regur; no option is proven by passage._

**geo_soils [hybrid] score 2 key OK not sensible H4 H5 H6**: Why is laterite soil formed in such areas?  
  - Because alluvial soil is the most widespread  
  - Because india has many types of soil  
  - Because soil is a very important resource  
  ✅ Because of high temperature and heavy rainfall  
  _Correct key, but distractors are off-topic passage sentences; 'such areas' is vague, so D stands out._

**geo_soils [hybrid_mis] score 2 key OK not sensible H4 H5 H6**: Why is laterite soil formed in such areas?  
  - Because soil is formed only from the weathering of rocks  
  ✅ Because of high temperature and heavy rainfall  
  - Because alluvial soil is only found in the Northern Plains  
  - Because laterite soil is fertile and good for most crops  
  _Key is right but it's a recall item; distractors are unrelated sentences, and B is the only on-topic option._

**geo_sundarbans_ocr [hybrid_mis] score 2 key OK not sensible H4 H5 H6**: Why do mangroves have special roots?  
  - Because tree roots prevent erosion by physically grabbing every grain of soil  
  ✅ Because these roots help plants breathe  
  - Because mangroves are only found in the ocean  
  - Because thorn forests grow in areas with heavy rainfall  
  _Distractors off-topic (erosion, thorn forests); B is the only on-topic option; 'roots' and 'breathe' leak._

**geo_sundarbans_ocr [hybrid] score 1 key OK not sensible H3 H4 H5 H6**: Why do mangroves have special roots?  
  - Because one of the most common mangroves there  
  ✅ Because these roots help plants breathe  
  - Because birds are also found there  
  - Because mangroves have special roots that solve this problem  
  _D restates the question and is arguably correct; A and C are broken, off-logic distractors._

**his_1857 [hybrid] score 2 key OK not sensible H1 H4 H5**: Why were the soldiers offended by the cartridges?  
  - Because local rulers joined the soldiers  
  ✅ Because they had to bite open the cartridges before using them  
  - Because began as a rising of Indian soldiers  
  - Because a young soldier named Mangal Pandey attacked his officers at Barrackpore  
  _Near-verbatim recall; distractors are ungrammatical fragments or irrelevant; B is the only fitting option._

**his_1857 [hybrid] score 2 key OK not sensible H4 H5**: Why did the British bring in more troops?  
  - Because the cartridges had to be bitten open before use  
  ✅ Because the rebels lacked a plan and modern weapons  
  - Because began as a rising of Indian soldiers  
  - Because bahadur Shah Zafar was sent to Rangoon  
  _Key correct, but C is a grammatical fragment and D is irrelevant; B stands out._

**his_1857 [hybrid_mis] score 2 key OK not sensible H4 H5**: Why did the British bring in more troops?  
  - Because christian missionaries were employees of the British government  
  - Because the British East India Company continued to rule India until 1947  
  - Because only the sepoys were unhappy with the British  
  ✅ Because the rebels lacked a plan and modern weapons  
  _Key correct; A and B are off-topic or outside the passage; D is the only on-topic option._

**his_1857 [hybrid] score 1 key OK not sensible H1 H3 H4 H5 H6**: Why was the revolt of 1857 a challenge to British rule?  
  - Because delhi was recaptured in September 1857  
  ✅ Because it challenged British rule in India in the nineteenth century  
  - Because a young soldier named Mangal Pandey attacked his officers at Barrackpore  
  - Because the cartridges had to be bitten open before use  
  _Key restates the question (circular), leaks the answer; other options are also plausible challenges._

**his_1857 [hybrid_mis] score 1 key OK not sensible H1 H3 H4 H5 H6**: Why was the revolt of 1857 a challenge to British rule?  
  - Because bahadur Shah Zafar was a powerful military general who planned the revolt  
  ✅ Because it challenged British rule in India in the nineteenth century  
  - Because the British East India Company continued to rule India until 1947  
  - Because the revolt happened only  
  _Circular key leaks the question; D is an incomplete fragment; A and C are silly or outside-passage._

**his_1857 [hybrid_mis] score 2 key OK not sensible H1 H4 H5**: Why were the soldiers offended by the cartridges?  
  - Because local rulers joined the soldiers  
  - Because a young soldier named Mangal Pandey attacked his officers at Barrackpore  
  - Because began as a rising of Indian soldiers  
  ✅ Because they had to bite open the cartridges before using them  
  _Recall; distractors are fragments or irrelevant events; D is the only on-topic option._

**his_ashoka [hybrid_mis] score 2 key OK not sensible H4 H5**: Why did Ashoka decide not to fight a war of conquest?  
  ✅ Because he felt sorrow for the suffering he saw  
  - Because the Sarnath lion capital was a throne where Ashoka sat to give orders  
  - Because the Dhamma Mahamattas were soldiers sent to fight wars and punish rebels  
  - Because kalinga was a small village that Ashoka conquered easily  
  _Correct is A, but distractors are off-topic passage-unrelated fragments; only A is on-topic._

**his_ashoka [hybrid_mis] score 1 KEY WRONG not sensible H3 H4 H5**: Why did Ashoka become king?  
  - Because chanakya was the king of the Mauryan Empire  
  ✅ Because he was the grandfather of Chandragupta Maurya, who founded the Mauryan dynasty  
  - Because chandragupta Maurya was Ashoka's son and became king after him  
  - Because the Sarnath lion capital was a throne where Ashoka sat to give orders  
  _Passage never says why he became king; key B is false (he was grandson)._

**his_ashoka [hybrid] score 1 KEY WRONG not sensible H3 H4 H2**: Why is the wheel on the national flag shown on the pillar?  
  - Because he turned to the teachings of the Buddha  
  ✅ Because it forms the national emblem of India today  
  - Because about eight years after he became king  
  - Because ashoka had his messages carved on rocks  
  _Passage does not explain why wheel is on flag; key B is circular nonsense._

**his_ashoka [hybrid] score 1 KEY WRONG not sensible H3 H4 H5**: Why did Ashoka become king?  
  - Because the wheel on it appears on our national flag  
  ✅ Because he was the grandfather of Chandragupta Maurya, who founded the Mauryan dynasty  
  - Because about eight years after he became king  
  - Because ashoka was one of the most famous rulers of ancient India  
  _Key B reverses the relationship; he was Chandragupta's grandson. No option correct._

**his_ashoka [hybrid] score 1 KEY WRONG not sensible H3 H4 H5**: Why did Ashoka decide not to fight a war of conquest?  
  - Because ashoka had his messages carved on rocks  
  ✅ Because he felt sorrow for the suffering he saw  
  - Because he turned to the teachings of the Buddha  
  - Because about eight years after he became king  
  _B and C both supported: sorrow, then turning to Buddha's teachings; distractors are fragments._

**his_ashoka [hybrid_mis] score 2 key OK not sensible H3 H4 H5**: Why did Ashoka fight a war against Kalinga?  
  ✅ Because he wanted to conquer Odisha and expand his empire  
  - Because the Dhamma Mahamattas were soldiers sent to fight wars and punish rebels  
  - Because kalinga was a small village that Ashoka conquered easily  
  - Because chandragupta Maurya was Ashoka's son and became king after him  
  _Passage says conquest aim only implicitly; distractors off-passage, A only on-topic option; leaks 'conquer'._

**his_chola [hybrid] score 1 key OK not sensible H1 H3 H4 H5 H6 H7**: Why did Rajaraja I become king?  
  - Because a figure is first made of wax  
  ✅ Because he became king in 985 CE  
  - Because he built a new capital called Gangaikondacholapuram  
  - Because they were centres of town life  
  _Key is only on-topic option; 'why' question is really recall; distractors are random passage fragments._

**his_chola [hybrid_mis] score 1 key OK not sensible H1 H4 H5 H6**: Why is the Brihadeeswara temple considered one of the largest temples in India?  
  ✅ Because its tower rises about 66 metres high  
  - Because chola temples were used only for worship and religious ceremonies  
  - Because buddhism disappeared from India  
  - Because kings attacked temples only  
  _Key is only on-topic option; distractors irrelevant (Buddhism, kings attacking temples); height leaks 'largest'._

**his_chola [hybrid] score 2 key OK not sensible H1 H4 H5**: Why is the Brihadeeswara temple considered one of the largest temples in India?  
  - Because he built a new capital called Gangaikondacholapuram  
  ✅ Because its tower rises about 66 metres high  
  - Because chola temples were not only places of worship  
  - Because the Cholas are especially remembered for their temples  
  _Distractors are passage fragments from other sentences, not misconceptions; tower height is plain recall._

**his_dandi [hybrid_mis] score 1 KEY WRONG not sensible H3 H4 H5 H6 H7**: Why did the movement start?  
  - Because the Non-Cooperation Movement and the Civil Disobedience Movement were exactly the same  
  ✅ Because people made salt from sea water, refused to buy foreign cloth  
  - Because the 'Quit India' movement was completely non-violent  
  - Because gandhi chose salt for the march  
  _No option is correct; B is a fragment, others off-topic; question vague._

**his_dandi [hybrid] score 3 key OK not sensible H5 H6**: Why did the Salt March show that ordinary people could challenge a powerful empire?  
  - Because women took part in large numbers  
  - Because simple act was the beginning of the Civil Disobedience Movement  
  ✅ Because they refused to obey an unjust law without using violence  
  - Because salt is something that every person  
  _Key correct but is only grammatical, complete option; B and D are fragments._

**his_dandi [hybrid_mis] score 1 KEY WRONG not sensible H3 H4 H5**: Why was salt a centre of India's struggle for freedom?  
  - Because the Salt March showed that ordinary people  
  - Because gandhi chose salt for the march  
  ✅ Because it was the main source of food and money in 1930  
  - Because simple act was the beginning of the Civil Disobedience Movement  
  _Key C is invented; passage says salt needed in food, not main source._

**his_dandi [hybrid] score 1 KEY WRONG not sensible H3 H4 H5**: Why was salt a centre of India's struggle for freedom?  
  - Because the Salt March showed that ordinary people  
  - Because simple act was the beginning of the Civil Disobedience Movement  
  ✅ Because it was the main source of food and money in 1930  
  - Because salt is something that every person  
  _Key C is invented, not in passage; others are fragments._

**his_dandi [hybrid_mis] score 2 key OK not sensible H4 H5 H6**: Why did Gandhi see the salt tax as a sign of unjust British rule?  
  - Because gandhi called off the Non-Cooperation movement  
  ✅ Because salt is needed by everyone  
  - Because gandhi chose salt for the march  
  - Because the British partitioned Bengal solely to make administration easier  
  _B is correct but the only on-topic option; distractors silly and unrelated._

**his_dandi [hybrid] score 2 key OK not sensible H4 H5 H6**: Why did Gandhi see the salt tax as a sign of unjust British rule?  
  ✅ Because salt is needed by everyone  
  - Because the protests continued peacefully  
  - Because they walked for 24 days  
  - Because the Salt March showed that ordinary people  
  _A correct but distractors are fragments; the form gives it away._

**his_dandi [hybrid_mis] score 3 key OK not sensible H5 H6**: Why did the Salt March show that ordinary people could challenge a powerful empire?  
  ✅ Because they refused to obey an unjust law without using violence  
  - Because simple act was the beginning of the Civil Disobedience Movement  
  - Because gandhi chose salt for the march  
  - Because salt is something that every person  
  _Correct, but others are fragments or irrelevant; form gives away the answer._

**his_dandi [hybrid] score 1 KEY WRONG not sensible H3 H4 H5**: Why did Gandhi break the salt law?  
  - Because the Salt March showed that ordinary people  
  ✅ Because he wanted to promote civil disobedience  
  - Because salt is something that every person  
  - Because women took part in large numbers  
  _Key B is vague; passage gives salt-law injustice, distractors are fragments._

**his_harappa [hybrid_mis] score 1 KEY WRONG not sensible H1 H3 H4 H5 H6**: Why is the citadel called the western part?  
  - Because all Harappan cities were exactly the same and had only two parts  
  - Because the first site of this civilisation to be discovered  
  ✅ Because it was smaller but higher and is called the citadel  
  - Because the Citadel was a military fort used for fighting wars  
  _Question premise false; citadel not 'called western'. Key C circular, no valid answer._

**his_harappa [hybrid_mis] score 1 KEY WRONG not sensible H1 H3 H4 H5 H6**: Why were the cities in the text described as having carefully planned drains?  
  - Because when the cities ended, all the Harappan people died out  
  - Because all Harappan cities were exactly the same and had only two parts  
  ✅ Because they were built with proper drainage systems  
  - Because each house's drain was connected to these street drains  
  _Key C restates question (circular); D is the actual evidence. Distractors off-topic._

**his_harappa [hybrid] score 1 KEY WRONG not sensible H1 H3 H4 H5**: Why are these cities important?  
  - Because the western part was smaller  
  - Because they were one or two storeys high  
  ✅ Because they were divided into two parts  
  - Because the cities had carefully planned drains  
  _Vague question; all options are facts, none explains importance. Key arbitrary._

**his_harappa [hybrid_mis] score 3 key OK SENSIBLE H1 H4**: Why did the people of Dholavira build large reservoirs?  
  - Because when the cities ended, all the Harappan people died out  
  - Because ancient people didn't care about hygiene  
  - Because other important cities included Mohenjodaro  
  ✅ Because the region was dry  
  _Correct, from 'because dry'; near recall, distractors irrelevant to reservoirs._

**his_harappa [hybrid_mis] score 1 KEY WRONG not sensible H1 H3 H4 H5**: Why are these cities important?  
  - Because all Harappan cities were exactly the same and had only two parts  
  ✅ Because they were divided into two parts  
  - Because when the cities ended, all the Harappan people died out  
  - Because the dockyard at Lothal was for small fishing boats only  
  _Vague question; key B merely a fact, not why important. Weak distractors._

**his_harappa [hybrid] score 1 KEY WRONG not sensible H1 H3 H4 H5 H6**: Why is the citadel called the western part?  
  - Because the first site of this civilisation to be discovered  
  - Because much of what we know comes from the remains of buildings  
  ✅ Because it was smaller but higher and is called the citadel  
  - Because each house's drain was connected to these street drains  
  _False premise; key C circular. Distractors unrelated to question._

**his_harappa [hybrid] score 3 key OK SENSIBLE H1 H4**: Why did the people of Dholavira build large reservoirs?  
  - Because the western part was smaller  
  - Because other important cities included Mohenjodaro  
  - Because the eastern part was larger  
  ✅ Because the region was dry  
  _Correct answer D; recall-ish, distractors are unrelated passage facts, not misconceptions._

**his_harappa [hybrid] score 1 KEY WRONG not sensible H1 H3 H4 H6**: Why were the cities in the text described as having carefully planned drains?  
  - Because many of these cities were divided into two parts  
  - Because each house's drain was connected to these street drains  
  ✅ Because they were built with proper drainage systems  
  - Because other important cities included Mohenjodaro  
  _Key C circular restatement; B also supports drain planning, so two defensible._

**his_mughal [hybrid_mis] score 2 KEY WRONG not sensible H1 H3 H4 H5**: Why did the mansabdar hold a position in the emperor's service?  
  ✅ Because he was given a rank called zat  
  - Because they needed a system to manage it  
  - Because zat rank refers to the number of elephants an officer owned  
  - Because mansabdars lived in and ruled their jagirs like kings  
  _Circular question; key doesn't answer why; option B has no referent, C is silly._

**his_mughal [hybrid] score 2 key OK not sensible H1 H4 H5 H6**: Why did Akbar organize an effective system of administration?  
  - Because allowed them to collect taxes from certain areas  
  ✅ Because he needed a system to manage his empire  
  - Because carried out a careful survey of crop yields  
  - Because akbar also followed a policy called sulh-i kul  
  _Recall of passage line; distractors are ungrammatical fragments, B only complete option._

**his_mughal [hybrid] score 2 key OK not sensible H1 H4 H5**: Why did Mansabdars have to maintain a fixed number of horsemen?  
  - Because mansabdars did not live in their jagirs  
  - Because the area cultivated over ten years  
  ✅ Because they were part of the army  
  - Because mansabdars were not paid in cash  
  _Option B is a fragment; distractors are unrelated passage facts, not misconceptions._

**his_mughal [hybrid] score 2 key OK not sensible H1 H4 H5 H6**: Why did Akbar follow the policy of universal peace?  
  - Because a mansabdar was a person who held a mansab  
  ✅ Because it did not discriminate between people of different religions  
  - Because wrote a history of his reign called the Akbar Nama  
  - Because he also had to maintain a fixed number of horsemen  
  _Restates the definition; distractors are fragments or unrelated facts, no misconceptions._

**his_mughal [hybrid_mis] score 3 key OK not sensible H1 H5**: Why did Akbar follow the policy of universal peace?  
  - Because wrote a history of his reign called the Akbar Nama  
  ✅ Because it did not discriminate between people of different religions  
  - Because sulh-i kul was a new religion that Akbar forced everyone to join  
  - Because akbar wrote the Akbar Nama to record his own achievements  
  _Near-recall; C is a good misconception but A is an ungrammatical fragment._

**his_mughal [hybrid_mis] score 3 key OK SENSIBLE H1 H4 H5**: Why did Akbar organize an effective system of administration?  
  - Because the eldest son of a Mughal emperor always inherited the throne  
  ✅ Because he needed a system to manage his empire  
  - Because the Zabt system was used for revenue collection across the entire Mughal empire  
  - Because the Mughal Empire became small and weak during Aurangzeb's reign  
  _Recall; B is the only option using passage wording; distractors off-topic._

**phy_circuit [hybrid_mis] score 2 key OK not sensible H1 H4 H5 H6**: Why do bulbs in a series circuit go off when one fuses?  
  ✅ Because the path is broken and all other bulbs go off too  
  - Because electric current is consumed or used up by the bulb in a circuit  
  - Because in a series circuit, the bulb closer to the positive terminal glows brighter  
  - Because a circuit is closed  
  _Key restates question; distractors off-topic or junk (D); recall of sentence._

**phy_circuit [hybrid] score 2 key OK not sensible H1 H4 H5**: Why are the lights and fans in parallel connected?  
  - Because a switch is used to open or close this path  
  - Because bulbs can also be joined one after another in a single path  
  - Because just as much current returns to the cell as leaves it  
  ✅ Because each one can be switched on or off without affecting the others  
  _Verbatim recall; distractors are unrelated passage sentences, not misconceptions._

**phy_circuit [hybrid] score 1 key OK not sensible H3 H4 H6**: Why does the circuit glow when the switch is on?  
  ✅ Because the current flows through the circuit  
  - Because a simple electric circuit needs three things  
  - Because they are joined in parallel  
  - Because fans are not joined in series  
  _Key vague, circular; 'circuit glows' wrong premise; distractors irrelevant to question._

**phy_circuit [hybrid_mis] score 2 key OK not sensible H1 H4 H5**: Why are the lights and fans in parallel connected?  
  - Because the glass of the bulb is what produces the light  
  ✅ Because each one can be switched on or off without affecting the others  
  - Because adding more resistors in parallel increases the total resistance of the circuit  
  - Because a switch stores electricity when it is in the OFF position  
  _Recall; distractors off-topic (glass, resistors, switch stores); correct only on-topic._

**phy_circuit [hybrid] score 2 key OK SENSIBLE H1 H4 H6**: Why do bulbs in a series circuit go off when one fuses?  
  - Because a switch is used to open or close this path  
  ✅ Because the path is broken and all other bulbs go off too  
  - Because just as much current returns to the cell as leaves it  
  - Because each one can be switched on or off without affecting the others  
  _Recall; distractors are random passage sentences; key echoes question wording._

**phy_circuit [hybrid_mis] score 1 KEY WRONG not sensible H3 H4 H8**: Why is a simple electric circuit important?  
  - Because a battery is just another name for a single electric cell  
  ✅ Because it allows current to flow and create electricity  
  - Because electric current is consumed or used up by the bulb in a circuit  
  - Because in a series circuit, the bulb closer to the positive terminal glows brighter  
  _Key says circuit 'create electricity', false; passage never says importance._

**phy_circuit [hybrid] score 1 KEY WRONG not sensible H3 H4**: Why is a simple electric circuit important?  
  - Because the current is not used up on the way  
  ✅ Because it allows current to flow and create electricity  
  - Because the longer line stands for the positive terminal  
  - Because a switch is used to open or close this path  
  _Passage never states importance; key 'create electricity' wrong; others also true statements._

**phy_friction [hybrid_mis] score 2 key OK not sensible H4 H5 H6**: Why do we feel warm when we rub our palms together?  
  - Because a car could not stop  
  ✅ Because friction produces heat  
  - Because friction only produces heat when you rub things very fast  
  - Because the driver presses the brakes  
  _Key leaks 'warm/heat'; A and D are off-topic junk; C is a nonsense hedge distractor._

**phy_friction [hybrid] score 1 key OK not sensible H4 H5**: Why does a rough surface produce more friction than a polished surface?  
  - Because the driver presses the brakes  
  ✅ Because it has larger bumps  
  - Because a car could not stop  
  - Because friction is not always a nuisance  
  _All three distractors are irrelevant non-sequiturs; answer obvious by form._

**phy_friction [hybrid] score 1 key OK not sensible H4 H5 H6**: Why do we feel warm when we rub our palms together?  
  - Because the driver presses the brakes  
  ✅ Because friction produces heat  
  - Because a car could not stop  
  - Because friction is not always a nuisance  
  _Distractors are irrelevant passage fragments; key is the only on-topic option._

**phy_friction [hybrid] score 1 key OK not sensible H1 H2 H4 H5**: Why is friction important?  
  - Because the harder the two surfaces are pressed together  
  - Because grease are put between the moving parts of machines  
  - Because ball bearings are fitted in the wheels of cycles  
  ✅ Because friction helps us walk, drive cars, and produce heat  
  _Vague stem; A–C ungrammatical fragments; D longest and only complete answer._

**phy_friction [hybrid_mis] score 2 key OK not sensible H4 H5**: Why is friction important?  
  ✅ Because friction helps us walk, drive cars, and produce heat  
  - Because perfectly smooth surfaces have zero friction  
  - Because rolling friction is zero  
  - Because friction only produces heat when you rub things very fast  
  _Vague stem; distractors are false-but-unrelated to importance; A longest and only on-topic._

**phy_magnets [hybrid] score 1 KEY WRONG not sensible H1 H3 H4 H5 H6**: Why does a bar magnet point in the north-south direction?  
  - Because materials that are attracted by a magnet are called magnetic materials  
  ✅ Because it always points in that direction when hung freely from a thread  
  - Because magnets lose their magnetism if they are heated  
  - Because each broken piece becomes a new magnet with its own north  
  _Passage never explains why; key B just restates the question (circular); distractors are irrelevant facts._

**phy_magnets [hybrid] score 2 key OK not sensible H1 H4 H5**: Why are some materials called magnetic materials?  
  - Because property is used in a compass  
  ✅ Because they are attracted by a magnet  
  - Because like poles repel each other  
  - Because magnets attract objects made of iron  
  _Pure definition recall; A is ungrammatical, so B is the only well-formed fit; distractors are off-topic fragments._

**phy_magnets [hybrid_mis] score 2 key OK not sensible H1 H4 H5**: Why are some materials called magnetic materials?  
  - Because magnetic field lines are real physical threads that exist around a magnet  
  ✅ Because they are attracted by a magnet  
  - Because all metals are attracted to magnets  
  - Because the magnetic field is strongest at the center of a bar magnet  
  _Definition recall; distractors off-topic or not in the passage (field lines); B is the only on-topic option._

**phy_magnets [hybrid_mis] score 1 KEY WRONG not sensible H1 H3 H4 H5 H6**: Why does a bar magnet point in the north-south direction?  
  ✅ Because it always points in that direction when hung freely from a thread  
  - Because magnetic field lines are real physical threads that exist around a magnet  
  - Because the center of a bar magnet is the strongest part  
  - Because all metals are attracted to magnets  
  _Key A is circular, with no causal explanation; the distractors are off-topic, and the fact is not in the passage._

**phy_mirror [hybrid_mis] score 1 KEY WRONG not sensible H1 H3 H4 H5 H6**: Why does the image appear 4 metres away from you when you stand 2 metres in front of a mirror?  
  - Because if you walk away from a plane mirror, your image gets smaller  
  ✅ Because of the mirror's symmetry, the image is laterally inverted  
  - Because a mirror image is just a person standing behind a transparent glass  
  - Because lateral inversion means the image is upside down  
  _Correct reason is image as far behind mirror as object in front; B is a non-sequitur._

**phy_mirror [hybrid] score 1 key OK not sensible H4 H5**: Why is the word AMBULANCE written in reverse on the front of ambulances?  
  - Because will be reflected at 30 degrees  
  - Because line is called the normal  
  - Because 4 metres away from you  
  ✅ Because the image is laterally inverted  
  _Key is right, but distractors are ungrammatical passage fragments; D is the only sensible option._

**phy_mirror [hybrid] score 1 KEY WRONG not sensible H3 H4 H5**: Why does the image appear 4 metres away from you when you stand 2 metres in front of a mirror?  
  ✅ Because of the mirror's symmetry, the image is laterally inverted  
  - Because the normal is the angle of incidence  
  - Because the ray that bounces back is called the reflected ray  
  - Because the second law says that the incident ray  
  _Lateral inversion doesn't explain the 4 m distance; distractors are fragments._

**phy_mirror [hybrid_mis] score 1 key OK not sensible H4 H5**: Why is the word AMBULANCE written in reverse on the front of ambulances?  
  - Because line is called the normal  
  ✅ Because the image is laterally inverted  
  - Because will be reflected at 30 degrees  
  - Because 4 metres away from you  
  _Key is right, but distractors are ungrammatical fragments; only B is coherent._

**phy_pressure [hybrid_mis] score 1 key OK not sensible H1 H3 H4 H5 H6 H7**: Why did Meena see many things?  
  - Because only living things like humans or animals can exert a force  
  ✅ Because the same idea explains many things  
  - Because a blunt knife has a wider edge  
  - Because the load is easier to carry  
  _Nonsensical question; key is a circular restatement; distractor A is silly and longest._

**phy_pressure [hybrid] score 1 KEY WRONG not sensible H1 H3 H4 H5**: Why did Meena learn the reason in her science class?  
  - Because meena watched her grandfather cut vegetables in the kitchen  
  - Because the same idea explains many things Meena had seen  
  - Because the sharp edge of a knife has a very small area  
  ✅ Because pressure is the force acting on a unit area of a surface  
  _Question is incoherent; key D is not a reason; B or C equally plausible._

**phy_pressure [hybrid] score 1 KEY WRONG not sensible H1 H3 H4 H6**: Why does the pressure increase with depth in water?  
  - Because the force from Grandfather's hand produces a large pressure  
  ✅ Because water pressure increases with depth in a liquid  
  - Because the same force spreads over a larger area  
  - Because the pressure on the head is reduced  
  _Key just restates the question; passage gives no reason; distractors off-topic._

**phy_pressure [hybrid_mis] score 1 KEY WRONG not sensible H1 H3 H4 H5 H6**: Why does the pressure increase with depth in water?  
  - Because pressure and Force are exactly the same thing  
  ✅ Because water pressure increases with depth in a liquid  
  - Because liquid pressure only acts downwards towards the bottom of the container  
  - Because fluids only exert pressure in the downward direction  
  _Key restates the question; no reason given; distractors are about direction, not depth._

**phy_pressure [hybrid_mis] score 1 KEY WRONG not sensible H1 H3 H4 H5**: Why did Meena learn the reason in her science class?  
  - Because meena watched her grandfather cut vegetables in the kitchen  
  - Because school bags have broad straps for the same reason  
  - Because the sharp edge of a knife has a very small area  
  ✅ Because pressure is the force acting on a unit area of a surface  
  _Incoherent question; key D is a definition, not a reason; options mismatched._

**phy_sound [hybrid_mis] score 2 key OK not sensible H1 H4 H5 H6**: Why do we hear different types of sounds?  
  - Because a high pitch sound is always louder than a low pitch sound  
  ✅ Because different frequencies are heard, like a whistle and a drum  
  - Because humans can hear any sound  
  - Because high-pitched sounds are always louder than low-pitched sounds  
  _Key restates question via whistle/drum; A and D near-duplicates; C silly; weak diagnostic_

**phy_sound [hybrid_mis] score 1 KEY WRONG not sensible H3 H1**: Why do we hear sound?  
  ✅ Because sound needs a medium to travel  
  - Because sound travels fastest in air  
  - Because humans can hear any sound  
  - Because sound is a physical substance that flows through the air like a gas  
  _Passage never says why we hear sound; medium option answers a different question_

**phy_sound [hybrid] score 2 key OK not sensible H1 H4 H5 H6**: Why do we hear different types of sounds?  
  - Because the number of vibrations in one second is called the frequency  
  - Because sounds below this range are called infrasonic  
  - Because dolphins can hear ultrasonic sounds  
  ✅ Because different frequencies are heard, like a whistle and a drum  
  _Distractors are true but irrelevant passage facts; key only fitting answer; weak_

**phy_sound [hybrid_mis] score 3 key OK not sensible H5**: Why do we hear a sound when we pluck a string of a sitar?  
  - Because sound waves move up and down like waves on a string  
  ✅ Because the vibration of the string produces sound  
  - Because humans can hear any sound  
  - Because we produce sound using only our mouth and tongue  
  _Key correct but is the only on-topic option; C silly; B copies passage wording_

**phy_sound [hybrid] score 1 KEY WRONG not sensible H3 H4**: Why do we hear sound?  
  - Because sound is produced by the voice box  
  - Because dolphins can hear ultrasonic sounds  
  ✅ Because sound needs a medium to travel  
  - Because a low frequency gives a low-pitched sound  
  _Medium need doesn't explain why we hear sound; question mismatched; distractors irrelevant facts_

**phy_sound [hybrid] score 2 key OK not sensible H4 H5**: Why do we hear a sound when we pluck a string of a sitar?  
  - Because a low frequency gives a low-pitched sound  
  ✅ Because the vibration of the string produces sound  
  - Because sound travels faster in solids than in air  
  - Because sound is produced by the voice box  
  _Distractors are unrelated passage facts, not misconceptions; key only on-topic option_

**phy_sound [hybrid] score 2 key OK not sensible H3 H4**: Why do we hear the tap through the wood?  
  ✅ Because sound travels faster in solids than in air  
  - Because a vibration is a rapid to-and-fro motion  
  - Because a high frequency gives a high-pitched sound  
  - Because sound is produced by the voice box  
  _Faster speed doesn't explain hearing clearly; distractors unrelated passage sentences_

**phy_sound [hybrid_mis] score 2 key OK not sensible H3 H4 H5**: Why do we hear the tap through the wood?  
  - Because humans can hear any sound  
  ✅ Because sound travels faster in solids than in air  
  - Because humans can hear ultrasound if it is played at a very high volume  
  - Because noise pollution only affects our ears and hearing ability  
  _Key weakly fits 'why hear'; distractors silly or off-topic; key only on-topic_
