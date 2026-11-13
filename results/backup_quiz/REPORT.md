# Backup quiz (plain Qwen3-0.6B, one call per question) on the 40 eval passages

Judge: Sonnet against docs/QUESTION_RUBRIC.md, blind to variant and to kept/rejected.

| Variant | Passages with >= 3 questions | Questions shown | Key correct | Score >= 4 (good) | Score <= 2 (bad) | Pi time per quiz (est. 60/20 tok/s), median / max |
|---|---|---|---|---|---|---|
| v3 | 34/40 | 134 | 104/134 | 0/134 | 128/134 | 51.2 s / 81.1 s |
- **v3: sensible 8/134** (key right, all options on topic and grammatical, answer not obvious; the lower, practical bar)

## Did the self-check help? (rejected-by-self-check questions vs shown ones, same judge)

- v3: questions the self-check threw out had a correct key 10/19 times, score >= 4 in 0/19

## Why questions were rejected

- v3: NOT question x2
- v3: answer is clearly the longest option x1
- v3: answer only repeats the question x20
- v3: answer too long x36
- v3: not enough wrong options x4
- v3: self-check failed x19
- v3: unclear it/they question x12

## Every shown question with its grade

**bio_digestion [v3] score 3 key OK not sensible H1 H5 H6**: Why does the inner lining of the stomach release hydrochloric acid and digestive juices?  
  - Because bile is produced by the stomach to digest all types of food  
  - Because food is converted into energy inside the stomach  
  ✅ Because the acid kills bacteria that enter with the food  
  - Because the partly digested food passes into the small intestine  
  _Key is correct and passage-provable, but it's near-verbatim recall and the only on-topic option. Distractors are off-topic._

**bio_digestion [v3] score 2 key OK not sensible H1 H4 H5 H6**: Why do we chew food?  
  - Because undigested food moves into the large intestine  
  ✅ Because our teeth break food into small pieces  
  - Because milk teeth have no roots and that is why they fall out  
  - Because humans could digest grass if we just chewed it  
  _Answer 'teeth break food into small pieces' is leaked by 'chew'; distractors are silly or off-topic._

**bio_digestion [v3] score 1 KEY WRONG not sensible H3 H4 H5**: Why does the large intestine absorb water and some salts?  
  - Because digestion only happens in the stomach  
  - Because the large intestine is where the most important nutrients are absorbed  
  - Because the partly digested food passes into the small intestine  
  ✅ Because the remaining waste is removed from the body through the anus  
  _Marked D is only a fact about waste removal, not a reason. The passage doesn't state why._

**bio_digestion [v3] score 1 KEY WRONG not sensible H3 H4 H5**: Why does the food pass from the stomach to the small intestine?  
  - Because food is converted into energy inside the stomach  
  - Because the tongue mixes the food with saliva  
  ✅ Because it is digested and processed by the small intestine  
  - Because bile is produced by the stomach to digest all types of food  
  _Marked C is circular and not in the passage. Passage gives no reason for the move._

**bio_heart [v3] score 2 key OK not sensible H4 H5 H6 H7**: Why do blood leaves the heart through arteries with thick, elastic walls?  
  - Because all arteries carry oxygen-rich blood and all veins carry carbon dioxide-rich blood  
  ✅ Because the blood in them is under high pressure  
  - Because the left and right sides of the heart are connected  
  - Because each contraction of the heart is a heartbeat  
  _Grammar error; B is the only on-topic option; D and C are irrelevant; A is long._

**bio_heart [v3] score 1 KEY WRONG not sensible H3 H4 H5 H7**: Why is the pulse rate higher in children?  
  - Because the blood in them is under high pressure  
  ✅ Because they have a higher heart rate at rest  
  - Because the heart is the organ where blood is actually created  
  - Because pulse and heartbeat are two completely different and unrelated processes  
  _Passage never says why; B is circular restatement; D is absurd and long._

**bio_microbes [v3] score 2 key OK not sensible H1 H4 H5 H6**: Why does curd form in milk?  
  ✅ Because a bacterium converts milk into curd  
  - Because other microorganisms break down dead plants  
  - Because the bacteria in curd are 'bad' germs, but we eat them anyway  
  - Because pasteurized milk is completely free of all microorganisms  
  _Recall; key leaks 'bacterium/curd'; distractors off-topic or silly; A only on-topic._

**bio_microbes [v3] score 2 key OK not sensible H1 H4 H5 H6**: Why do antibiotics work against disease-causing bacteria?  
  - Because the same kind of bacteria helps in making cheese  
  - Because taking antibiotics makes my body's immune system stronger for the future  
  - Because antibiotics are effective treatments for the common cold and flu  
  ✅ Because they kill or stop the growth of disease-causing bacteria  
  _Key restates question; D longest; distractors off-topic or unrelated to the question._

**bio_microbes [v3] score 2 key OK not sensible H1 H4 H6**: Why do the dough rise and the batter become soft and spongy?  
  - Because a bacterium called Lactobacillus multiplies in the milk  
  ✅ Because as yeast respires, it releases carbon dioxide gas  
  - Because smoke is a gas, just like oxygen or nitrogen  
  - Because air is mostly made of oxygen  
  _Recall of the sentence; distractors irrelevant (smoke, air); question leaks 'rise'/'gas'._

**bio_microbes [v3] score 1 KEY WRONG not sensible H1 H2 H3 H4 H5**: Why are microorganisms small?  
  ✅ Because they are living things  
  - Because viruses are just a very small type of bacteria  
  - Because although some cause diseases  
  - Because all microorganisms are harmful germs that cause diseases  
  _Passage never says why they are small; A is circular, C is a fragment._

**bio_pitcher [v3] score 2 key OK not sensible H1 H4 H5 H6**: Why can the insect not climb back out?  
  - Because the stem only carries water from the roots to the leaves  
  - Because only the colorful petals are part of the flower  
  - Because a few plants also trap insects  
  ✅ Because hair inside the pitcher points downwards  
  _Key correct, but distractors are off-topic passage fragments; the key repeats the passage wording and is the only on-topic option._

**bio_pitcher [v3] score 1 key OK not sensible H1 H4 H5 H6 H7**: Why does the pitcher rim attract insects?  
  - Because parasitic plants like Cuscuta help the host plant by sharing nutrients  
  ✅ Because it produces a sweet substance that attracts insects  
  - Because the insects are not its main source of food  
  - Because insectivorous plants eat insects  
  _The question leaks its answer ("attracts insects"), and the distractors are off-topic._

**bio_pitcher [v3] score 1 key OK not sensible H1 H4 H5 H7**: What happens when an insect lands on the rim?  
  - The answer lies in the soil  
  - Saprotrophs eat dead matter by swallowing it  
  - Only the colorful petals are part of the flower  
  ✅ It slips and falls inside  
  _Plain recall, and the distractors are unrelated, so the answer is the only on-topic option._

**bio_pitcher [v3] score 1 KEY WRONG not sensible H3 H4 H5**: Why do pitcher plants grow in soil that is poor in nitrogen?  
  ✅ Because they need nitrogen to make proteins  
  - Because a few plants also trap insects  
  - Because plants get their food from the soil through their roots  
  - Because plants can take nitrogen directly from the air through their leaves  
  _The passage says soil poor in nitrogen is why plants catch insects, not why they grow there. The key is wrong._

**bio_pollination [v3] score 2 key OK not sensible H1 H4 H5 H6**: Why is the stamen called the male part of a flower?  
  - Because pollen is the 'seed' of the flower  
  - Because insects such as bees  
  ✅ Because it produces pollen grains  
  - Because every flower has both male and female parts  
  _Recall; key echoes 'produces pollen'; option B is a sentence fragment, off-topic._

**bio_pollination [v3] score 2 key OK not sensible H1 H3 H4 H6**: Why do seeds get scattered?  
  - Because the female part is the pistil  
  ✅ Because they are scattered by wind, water  
  - Because seeds are non-living objects  
  - Because fertilisation occurs on the surface of the stigma  
  _Key is truncated fragment about how, not why; distractors irrelevant; 'scattered' leaks._

**bio_respiration [v3] score 2 key OK not sensible H1 H4 H5 H6**: What happens when oxygen is used?  
  - Oxygen turns into carbon dioxide inside the lungs  
  - We inhale pure oxygen and exhale pure carbon dioxide  
  - Respiration is what happens inside the cells of the body  
  ✅ The glucose is broken down completely into carbon dioxide  
  _Recall of sentence; key words leak in stem/option; distractors off-topic copies_

**bio_respiration [v3] score 2 key OK SENSIBLE H1 H4 H5 H6**: What happens when we breathe out?  
  - Air entering the lungs causes the chest to expand  
  - Glucose from our food is broken down to release energy  
  ✅ The chest cavity becomes smaller and air is pushed out  
  - Energy is produced in the lungs during breathing  
  _Pure recall; correct option copies passage and repeats stem words_

**bio_respiration [v3] score 2 key OK not sensible H4 H5 H7**: Why is respiration hidden during the day?  
  - Because respiration is what happens inside the cells of the body  
  ✅ Because photosynthesis uses up more carbon dioxide than respiration releases  
  - Because plants only respire at night when they are not doing photosynthesis  
  - Because anaerobic respiration is just  
  _Good target idea, but option D is truncated fragment; A is circular_

**bio_respiration [v3] score 2 key OK not sensible H3 H4 H5 H6**: Why do leg muscles produce lactic acid during hard exercise?  
  - Because the glucose is broken down completely into carbon dioxide  
  ✅ Because they respire anaerobically and produce lactic acid, causing cramps  
  - Because anaerobic respiration only happens in bacteria and yeast, not humans  
  - Because lactic acid is produced  
  _Key restates stem (lactic acid); D truncated; passage lacks the 'why' beyond anaerobic_

**bio_vaccine [v3] score 2 key OK not sensible H1 H4 H5 H6**: Why did James Phipps get slightly ill?  
  - Because vaccines are dangerous  
  - Because the bacteria in curd are 'bad' germs, but we eat them anyway  
  - Because an English doctor named Edward Jenner noticed something interesting in the countryside  
  ✅ Because he got a small cut from a cowpox sore on his hand  
  _D is the only on-topic option; B and C are irrelevant; D leaks 'cowpox sore'; recall._

**bio_vaccine [v3] score 1 KEY WRONG not sensible H3 H4 H5**: Why did Jenner expose the boy to smallpox?  
  - Because reducing a fever with medicine means the disease is cured  
  - Because vaccines are dangerous  
  ✅ Because he recovered from illness  
  - Because smallpox was declared eradicated in 1980  
  _Passage says Jenner tested the cowpox idea; 'he recovered' is a weak, off-topic fit, and distractors are irrelevant._

**bio_vaccine [v3] score 2 key OK not sensible H4 H5 H6 H3**: Why did Edward Jenner notice something interesting in the countryside?  
  - Because the Great Depression happened  
  - Because india was declared free of polio in 2014  
  ✅ Because he noticed that cowpox was not spreading among milkmaids  
  - Because potatoes, chilies, and maize have always been part of Indian and European diets  
  _Only on-topic option; irrelevant distractors; 'noticed' leaks; reason is milkmaids with cowpox not getting smallpox._

**bio_vaccine [v3] score 2 key OK not sensible H1 H4 H5**: What happens when the real germs attack later?  
  - All diseases are caused by germs or external microorganisms  
  - Smallpox was one of the most feared diseases in the world  
  ✅ The body can destroy them quickly, before they cause disease  
  - Vaccines are dangerous  
  _Direct recall; distractors off-topic or irrelevant, so correct option is obvious._

**bio_xylem [v3] score 2 key OK not sensible H1 H4 H5 H6**: Why is the phloem important in plant growth?  
  - Because plants get their food from the soil through their roots  
  ✅ Because it carries food from the leaves to other parts of the plant  
  - Because the main force that pulls it is transpiration  
  - Because phloem only moves food from the leaves down to the roots  
  _Recall; B is only option answering the 'why' in-topic; C is nonsensical, D is wrong._

**bio_xylem [v3] score 1 KEY WRONG not sensible H3 H4 H5 H6**: Why does a plant move water from its roots to leaves?  
  ✅ Because water travels through xylem  
  - Because phloem only moves food from the leaves down to the roots  
  - Because xylem can transport water in both upward and downward directions  
  - Because strengthened by a substance called lignin  
  _Question asks why; no option proves cause (transpiration pull). A is circular, D is ungrammatical._

**bio_xylem [v3] score 2 key OK not sensible H1 H4 H5 H6**: Why are the main cells of xylem dead when they do their job?  
  ✅ Because they lose their living contents and cross walls break down  
  - Because plants 'suck' water up through the xylem like a person using a straw  
  - Because dead cells in a plant are waste products and have no biological function  
  - Because the water travels through a tissue called xylem  
  _Key restates passage and leaks 'dead cells'; B and D are off-topic, C is outside the passage._

**chem_acids [v3] score 1 key OK not sensible H1 H3 H4 H5 H6 H7**: What happens when an acid is mixed with a base?  
  - Neutralisation results in the total disappearance of the acid and base  
  - A strong acid is the same  
  - Lemon juice contains citric acid  
  ✅ They cancel each other's effect  
  _A also arguably true; B and C are nonsense; D is recall and leaks via the question._

**chem_acids [v3] score 1 KEY WRONG not sensible H3 H4 H5 H8**: Why does blue litmus turn red in an acid?  
  - Because lemon juice contains citric acid  
  ✅ Because it changes color in an acidic solution  
  - Because when phenolphthalein turns colorless, the substance has been destroyed  
  - Because if litmus paper does not change color, the substance must be water  
  _B is circular; no option explains litmus; C and D are off-topic distractors._

**chem_acids [v3] score 2 key OK not sensible H1 H4 H5**: Why do we use indicators?  
  - Because a strong acid is the same  
  ✅ Because tasting is not a safe way to test a substance  
  - Because acids are always liquids  
  - Because turmeric is another natural indicator found in every Indian kitchen  
  _Recall of one sentence; B is the only on-topic option; D and A are off-topic._

**chem_acids [v3] score 2 key OK not sensible H1 H4 H5 H6**: Why do some foods taste sour?  
  - Because an indicator changes its colour  
  ✅ Because they contain acids  
  - Because all acids are dangerous and corrosive chemicals  
  - Because acids are always liquids  
  _Recall; the question's wording 'contain acids' is copied into B; distractors are weak._

**chem_changes [v3] score 1 key OK not sensible H1 H3 H4 H5 H6 H7**: What happens when a piece of paper burns?  
  - When wood burns, the matter is destroyed and nothing is left but ash  
  ✅ It turns into ash  
  - A chemical change only happens if you see an explosion or fire  
  - The wax first melts  
  _Recall; distractors off-topic or irrelevant; 'ash' leaks; B is the only on-topic option._

**chem_changes [v3] score 1 KEY WRONG not sensible H1 H3 H4 H5 H6**: What happens when a sheet of paper is cut into pieces?  
  - A substance changes its shape  
  ✅ Each piece is still paper  
  - When wood burns, the matter is destroyed and nothing is left but ash  
  - All physical changes can be reversed easily  
  _A and B both supported by passage; recall; off-topic distractor C; 'still paper' leaks._

**chem_changes [v3] score 1 key OK not sensible H1 H4 H5 H6**: What happens when baking soda is added to vinegar?  
  - A chemical change only happens if you see an explosion or fire  
  - Boiling water is a chemical change  
  - Water can be frozen back into ice  
  ✅ Bubbles of carbon dioxide gas are produced  
  _Plain recall; distractors unrelated to baking soda; D is the only on-topic option._

**chem_changes [v3] score 1 key OK not sensible H1 H4 H5 H6**: What happens when a candle burns?  
  - Combustion is a physical change  
  - A chemical change only happens if you see an explosion or fire  
  - Changes around us can be grouped into two kinds  
  ✅ The wax first melts, which is a physical change  
  _Recall; C is irrelevant; D is partial, since candle burning is both; 'candle' leaks._

**chem_combustion [v3] score 3 key OK not sensible H5 H4**: Why should water never be used on fires involving electrical equipment?  
  ✅ Because water conducts electricity and can give a shock  
  - Because water is the most common extinguisher  
  - Because water is the best way to put out an electrical fire  
  - Because air is the fuel that burns in a fire  
  _Correct, but D is off-topic and B/C are silly; the question gives away its key words._

**chem_combustion [v3] score 1 key OK not sensible H3 H4 H5 H7 H8**: Why is combustion possible?  
  ✅ Because a fuel, air  
  - Because the oil floats on water  
  - Because combustion is a physical change  
  - Because air is the fuel that burns in a fire  
  _Truncated key 'a fuel, air' is incomplete and ungrammatical; the distractors are irrelevant._

**chem_combustion [v3] score 2 key OK not sensible H4 H5 H6**: Why does kerosene catch fire easily?  
  - Because a substance with a high ignition temperature catches fire very easily  
  - Because carbon dioxide is the best extinguisher  
  ✅ Because it has a low ignition temperature  
  - Because spontaneous combustion happens without any reason or heat  
  _Option C repeats the question's wording; distractors B and D are off-topic and A is a flipped copy._

**chem_combustion [v3] score 2 key OK not sensible H1 H4 H5**: Why is water not suitable for oil and petrol fires?  
  - Because incomplete combustion only produces smoke, not any dangerous gases  
  ✅ Because the oil floats on water and keeps burning  
  - Because water is the most common extinguisher  
  - Because water is the best way to put out an electrical fire  
  _Near-verbatim recall of a passage sentence; distractors A, C and D are irrelevant, so B is obvious._

**chem_metals [v3] score 2 key OK not sensible H1 H4 H6**: Why do solid non-metals break into pieces when hammered?  
  - Because school bells are made of metal  
  ✅ Because they are soft and dull  
  - Because in a displacement reaction, the 'stronger' or 'heavier' metal wins  
  - Because rusting is a physical change  
  _Recall of one passage sentence; distractors off-topic/irrelevant; 'soft' hints answer._

**chem_metals [v3] score 2 key OK not sensible H4 H5 H6**: Why are cooking vessels made of metal and electric wires made of copper?  
  ✅ Because metals are good conductors of heat and electricity  
  - Because metals form oxides that are basic in nature  
  - Because in a displacement reaction, the 'stronger' or 'heavier' metal wins  
  - Because non-metals never conduct electricity  
  _Question wording leaks 'conductors'; two distractors irrelevant boilerplate; correct option longest._

**chem_metals [v3] score 1 key OK not sensible H1 H3 H4 H5 H6**: Why do metals form basic oxides?  
  - Because elements can be broadly divided into metals  
  ✅ Because they react with oxygen to form basic oxides  
  - Because all metal oxides are basic in nature  
  - Because all metals react with dilute acids to produce hydrogen gas  
  _Circular answer; option C also true from passage; 'basic oxides' leaked._

**chem_metals [v3] score 2 key OK not sensible H1 H4 H6**: Why is the school bell made of metal?  
  - Because any object that makes a sound when hit is sonorous  
  - Because mercury is a metal that is liquid at room temperature  
  ✅ Because metals also make a ringing sound when struck  
  - Because in a displacement reaction, the 'stronger' or 'heavier' metal wins  
  _Pure recall, answer leaks 'ringing sound'; distractors irrelevant to bells._

**chem_separation [v3] score 2 key OK not sensible H1 H2 H4 H5 H6**: Why is sedimentation used in separating mixtures?  
  - Because a sieve can separate a mixture of salt and sand  
  ✅ Because it separates solids from liquids, like sand in water  
  - Because sedimentation only works for mud and water mixtures  
  - Because sea water is let into shallow pits called salt pans  
  _Option B is the only on-topic option; the others are off-topic or copied irrelevant passage sentences, and the question names sedimentation's purpose vaguely._

**civ_bill [v3] score 1 KEY WRONG not sensible H1 H3 H4 H5 H6 H7**: Why is a bill often sent to a committee?  
  - Because a bill is voted on immediately after it is introduced, without any discussion  
  ✅ Because it is debated and members may suggest changes  
  - Because a bill becomes a law  
  - Because once both Houses have passed a bill  
  _Passage says committee studies bill in detail; no option says that. B is a different stage._

**civ_bill [v3] score 1 KEY WRONG not sensible H3 H4 H5 H6**: Why can a money bill be introduced only in Lok Sabha?  
  - Because the Rajya Sabha can reject a Money Bill passed by the Lok Sabha  
  - Because first the bill is read out  
  ✅ Because it deals with taxes and government spending  
  - Because only the Prime Minister can introduce a bill in Parliament  
  _Passage gives no reason for Lok Sabha-only; C merely restates what money bills deal with, and the key is unprovable._

**civ_bill [v3] score 2 key OK not sensible H1 H2 H3 H5 H6**: What happens when the President signs it and gives assent?  
  - A bill passed by both Houses of Parliament becomes a law automatically  
  - The House then discusses each part of the bill  
  ✅ The bill becomes an Act, which is a law  
  - The Rajya Sabha can reject a Money Bill passed by the Lok Sabha  
  _A also arguably correct (becomes law on assent); C restates the question's own words, so it is a recall and leak item._

**civ_bill [v3] score 2 key OK not sensible H1 H3 H4 H5**: What happens when a majority votes in favour?  
  - A bill passed by both Houses of Parliament becomes a law automatically  
  ✅ The bill is passed  
  - A bill becomes a law  
  - Members may suggest changes  
  _Pure recall; B repeats the passage. C and D are wrong but mismatched; A is not about voting._

**civ_panchayat [v3] score 2 key OK not sensible H5 H6 H4**: Why can the villagers question the sarpanch?  
  - Because local matters are managed by an elected body called the Gram Panchayat  
  - Because panchayat funds come only from the pocket money of the Sarpanch and members  
  - Because the Sarpanch is appointed by the district collector and not chosen by villagers  
  ✅ Because they can suggest new work and ask about money usage at meetings  
  _D is correct but restates the passage and leaks 'questions'; B, C are silly/contradictory distractors._

**civ_panchayat [v3] score 1 key OK not sensible H3 H4 H5 H6**: Why is the secretary of the Gram Panchayat not elected?  
  - Because ward councillors are appointed by the government, not elected  
  - Because the Gram Sabha consists only of the elected members of the Panchayat  
  - Because every adult who lives in the village  
  ✅ Because the government appoints him, not by election  
  _D is circular, leaks the question, and is the only coherent option. C is a fragment._

**civ_panchayat [v3] score 1 KEY WRONG not sensible H3 H4 H5**: Why is the Panchayat Samiti formed?  
  - Because decentralisation was introduced in India only in 1992 when local governments were created  
  - Because every adult who lives in the village  
  - Because panchayat funds come only from the pocket money of the Sarpanch and members  
  ✅ Because it is formed at the block level  
  _The passage does not say why it is formed. D just restates the level. B and C are fragments._

**civ_rights [v3] score 1 KEY WRONG not sensible H3 H4 H5 H1**: Why is freedom of speech included in the Right to Freedom?  
  - Because fundamental rights are absolute and can never be restricted  
  ✅ Because it allows people to express themselves freely  
  - Because without it all the other rights would have no value  
  - Because freedom of speech allows me to say anything I want, including inciting violence  
  _Passage never explains why speech is included; D is a joke; B is circular._

**civ_rights [v3] score 2 key OK not sensible H4 H5 H1**: Why is the right to constitutional remedies important?  
  - Because the NHRC can punish people who violate human rights  
  - Because right to Equality means everyone must be treated exactly the same  
  - Because everyone has equal access to public places such as parks  
  ✅ Because it ensures citizens can seek justice when their rights are violated  
  _Key is correct but off-topic distractors (NHRC, parks) make it a giveaway; the explanation is a paraphrase._

**civ_rights [v3] score 2 key OK not sensible H3 H4 H5 H1**: Why is the Cultural and Educational Rights important?  
  - Because fundamental rights are absolute and can never be restricted  
  - Because without it all the other rights would have no value  
  ✅ Because it allows minorities to preserve their culture and education  
  - Because only people who can read and write have the right to vote  
  _Key matches the passage, but the distractors are off-topic or reused, so it is a giveaway; also recall._

**civ_rights [v3] score 1 KEY WRONG not sensible H3 H4 H1**: Why is equality important in the text?  
  - Because dignity is something you earn through good behavior  
  ✅ Because equality is the foundation of justice and fairness in society  
  - Because right to Equality means everyone must be treated exactly the same  
  - Because the Constitution of India gives every citizen certain basic rights  
  _Passage never says equality is the foundation of justice; there is no correct option._

**civ_secularism [v3] score 1 key OK not sensible H1 H3 H4 H5 H6 H7**: Why is the law not requiring people riding two-wheelers to wear helmets?  
  - Because even though some people defended it as part of their religious tradition  
  - Because freedom of religion protects only the religion of the majority  
  - Because banning a practice like untouchability or sati hurts secularism  
  ✅ Because Sikhs who wear turbans are allowed to not wear helmets  
  _Question is garbled and inverted; D leaks answer; distractors are off-topic fragments._

**civ_secularism [v3] score 2 key OK not sensible H1 H3 H4 H6**: Why is the celebration of a religious festival not allowed in government schools?  
  - Because the government should never interfere in religious matters, even if they are harmful  
  ✅ Because students are free to celebrate at home, not in school  
  - Because sikhs who wear turbans are allowed not to wear a helmet  
  - Because if the government gives money to a religious school, it is not secular  
  _Key is weak, partial reasoning; C is a helmet fact irrelevant to schools; D off-topic._

**eco_money [v3] score 2 key OK not sensible H1 H4 H5 H6**: Why is money called a medium of exchange?  
  - Because people also keep money in banks as deposits  
  ✅ Because money acts as a go-between in exchanges  
  - Because modern paper money has intrinsic value like gold or silver  
  - Because money is valuable only  
  _Answer is the passage phrase; 'go-between' echoes the term; D is silly._

**eco_money [v3] score 2 key OK not sensible H1 H4 H5 H6**: Why is money used as a medium of exchange?  
  - Because money is valuable only  
  - Because people also keep money in banks as deposits  
  ✅ Because it acts as a go-between in exchanges  
  - Because modern paper money has intrinsic value like gold or silver  
  _Duplicate of Q1; word-spotting; weak joke-like distractors; shares 'medium of exchange' leak._

**eco_money [v3] score 1 key OK not sensible H1 H3 H4 H5 H7**: Why did people use the barter system?  
  - Because money is valuable only  
  - Because barter is efficient if you have enough goods to trade  
  - Because use the rest to give loans to people who need them  
  ✅ Because they exchanged goods directly for other goods  
  _Circular answer; 'Because use the rest' is ungrammatical; passage never says why._

**eco_shg [v3] score 3 key OK SENSIBLE H4**: Why did the bank lend money to the group?  
  - Because many poor people have nothing to offer  
  ✅ Because the members are responsible for repaying together  
  - Because the terms of credit are fixed by law  
  - Because money is valuable only  
  _Key correct, near-recall; distractors A, C, D weak/off-topic, D silly._

**eco_shg [v3] score 1 KEY WRONG not sensible H3 H4 H5 H6**: Why do banks ask for collateral?  
  - Because collateral is a fee paid to the bank for taking a loan  
  - Because members can take small loans from the group to meet their needs  
  ✅ Because they want to lend money to poor people who can't repay it  
  - Because money is valuable only  
  _Key C is wrong; collateral is for recovering unpaid loans. Distractors irrelevant._

**eco_shg [v3] score 2 key OK not sensible H1 H4 H5**: Why do members get loans from the group?  
  ✅ Because the group decides the purpose, amount, and repayment schedule  
  - Because the terms of credit are fixed by law  
  - Because collateral is a fee paid to the bank for taking a loan  
  - Because the bank lends to the group as a whole  
  _Key correct but phrase-matching recall; distractors B and C are off-topic._

**eco_unemployment [v3] score 1 KEY WRONG not sensible H1 H3 H4 H5 H6 H7**: Why does seasonal unemployment affect people in the harvest season?  
  - Because landless labourers are people who do not work  
  ✅ Because they work for four months and have no job during the harvest  
  - Because promises 100 days of paid work in a year to rural households  
  - Because seasonal unemployment happens only in farming  
  _Key B contradicts passage (no work after harvest); options ungrammatical, off-topic, and nonsensical._

**eco_unemployment [v3] score 2 key OK not sensible H4 H6 H5**: Why is this type of unemployment common in Indian agriculture?  
  ✅ Because many families share small pieces of land  
  - Because all farmers in India own the land they cultivate  
  - Because seasonal unemployment happens only in farming  
  - Because unemployment wastes a country's human resource  
  _Key correct, but 'common in Indian agriculture' is disguised unemployment; distractors C and D are irrelevant fragments; 'agriculture' and 'share' leak._

**eco_unemployment [v3] score 1 KEY WRONG not sensible H1 H3 H4 H5 H7**: Why is farming in many areas important?  
  ✅ Because it depends on the rain and provides work during sowing and harvesting  
  - Because farming work is the same amount in every month  
  - Because farmers have work throughout the entire year  
  - Because promises 100 days of paid work in a year to rural households  
  _Question about 'importance' is not answered by passage; key is a copy-paste; D is ungrammatical._

**eco_unemployment [v3] score 2 key OK not sensible H1 H4 H5 H6**: What happens when three of them stopped working on the farm?  
  ✅ The amount of grain produced would stay the same  
  - Farming work is the same amount in every month  
  - Farmers have work throughout the entire year  
  - Promises 100 days of paid work in a year to rural households  
  _Key is correct, but it is recall, and the answer leaks; options B-D are ungrammatical, irrelevant fragments._

**env_solar [v3] score 2 key OK not sensible H1 H3 H4 H5 H6**: Why is solar energy used in the production of electricity?  
  - Because solar panels need hot weather and give no electricity in cool weather  
  ✅ Because solar panels convert solar energy directly into electricity  
  - Because solar energy is renewable  
  - Because solar energy does not produce smoke or harmful gases  
  _Circular: 'convert directly into electricity' leaks key; options C and D also arguably true reasons; A silly._

**env_solar [v3] score 2 key OK not sensible H1 H4 H5**: What happens when sunlight falls on a solar cell?  
  - Solar panels produce no electricity at night  
  ✅ It produces a small electric current  
  - Solar panels give no power on cloudy days  
  - Solar energy is renewable  
  _Plain recall; distractors are unrelated passage sentences, not answers to the question; only B fits._

**env_solar [v3] score 2 key OK not sensible H1 H4 H5**: Why are many cells joined together in a panel?  
  - Because solar energy does not produce smoke or harmful gases  
  ✅ Because a single cell gives only about half a volt  
  - Because intermittency is a fatal flaw  
  - Because batteries create new electricity from nothing  
  _Recall; distractors off-topic or silly ('intermittency is a fatal flaw', batteries from nothing); B only fit._

**env_solar [v3] score 1 KEY WRONG not sensible H1 H2 H3 H4 H5**: Why is solar energy efficient at night?  
  - Because solar panels give no power on cloudy days  
  ✅ Because it produces no electricity at night and less on cloudy days  
  - Because the Sun is the main source of energy for the Earth  
  - Because solar energy is renewable  
  _False premise: solar is not efficient at night; no option is correct._

**env_waste [v3] score 3 key OK SENSIBLE H5**: Why is kitchen waste called biodegradable waste?  
  - Because burning plastic makes it biodegradable  
  - Because the waste is collected by municipal workers  
  ✅ Because tiny organisms in the soil can break it down  
  - Because biodegradable materials decompose almost instantly once thrown away  
  _Key correct, but it copies passage wording and D is longest; mostly definition recall._

**env_waste [v3] score 1 key OK not sensible H1 H3 H4 H5 H7**: Why do the waste end up in the dustbin?  
  - Because kitchen waste such as peels  
  ✅ Because they are thrown away every day  
  - Because when plastic breaks into tiny pieces, it has disappeared from the environment  
  - Because biodegradable materials decompose almost instantly once thrown away  
  _Trivial recall; distractors are off-topic, and the question is ungrammatical and ill-formed._

**env_waste [v3] score 1 key OK not sensible H3 H4 H5 H7**: Why do landfills become huge and smelly?  
  - Because toxins do not accumulate in predators  
  - Because biodegradable materials decompose almost instantly once thrown away  
  - Because refuse what you do not need  
  ✅ Because waste is not separated at home  
  _Passage never says unseparated waste makes landfills smelly; distractors are off-topic fragments._

**env_waste [v3] score 1 KEY WRONG not sensible H3 H4 H5**: Why is reducing plastic use important?  
  ✅ Because it helps reduce harmful gases and improves food security  
  - Because tiny organisms in the soil can break it down  
  - Because if plastic can be recycled, it is fine to use  
  - Because recycling is the only 'R' that matters for saving the environment from plastic  
  _'Improves food security' is unsupported, so no option is proven; the others are off-topic._

**geo_ghats [v3] score 2 key OK not sensible H5 H6 H4**: Why do the Western Ghats support thick evergreen forests?  
  ✅ Because they receive heavy rain from the monsoon  
  - Because uNESCO declared the Western Ghats a World Heritage Site in 2012  
  - Because thorn forests grow in areas with heavy rainfall  
  - Because tropical evergreen forests are found only in India's Western Ghats  
  _Key correct but 'heavy rain' copies passage wording, leaks via 'heavy rain'; B and C implausible._

**geo_ghats [v3] score 2 key OK not sensible H3 H4 H6**: Why are the Western Ghats important?  
  - Because the Tropic of Cancer makes all of India tropical  
  ✅ Because they supply water to millions of people in southern India  
  - Because the Western Ghats receive heavy rain from the south-west monsoon  
  - Because tropical evergreen forests are found only in India's Western Ghats  
  _Option C also supported (rain), vague 'important'; A and D off-topic distractors._

**geo_ghats [v3] score 1 key OK not sensible H1 H2 H3 H4 H6 H8**: Why are the examples given in the text included?  
  ✅ Because they are examples of endemic species  
  - Because scientists call such places biodiversity hotspots  
  - Because endemic species are those that are found everywhere in the world  
  - Because endangered species are the same  
  _Vague question about 'text'; options not tied to examples, distractors silly, key leaks._

**geo_groundwater [v3] score 3 key OK SENSIBLE H5 H1**: Why is water table dropping in many parts of India?  
  - Because water that runs off or evaporates from a field is not really lost  
  ✅ Because water is pumped out faster than it can be replenished by rainfall  
  - Because the upper level of this water-filled layer is called the water table  
  - Because drip irrigation gives plants more water than flooding the field  
  _Key correct but near-recall of passage sentence; option B longest and copies passage; distractors off-passage._

**geo_groundwater [v3] score 1 KEY WRONG not sensible H3 H1 H4 H5 H6**: Why do people think groundwater flows in underground rivers or lakes?  
  - Because groundwater is stored in large empty underground swimming pools or rivers  
  ✅ Because they imagine it, but it's mostly not true  
  - Because groundwater is a big underground lake or river  
  - Because some of the water soaks into the ground  
  _Key is circular, not a reason; passage never says why people think this; options leak._

**geo_groundwater [v3] score 1 KEY WRONG not sensible H3 H4 H5**: Why is infiltration important?  
  - Because harvested rainwater is useful only for storing in tanks, not for refilling groundwater  
  - Because the water table is not fixed  
  ✅ Because it helps water reach the ground  
  - Because rainwater harvesting is only useful in places that get very heavy rain  
  _Key 'helps water reach the ground' is vague/weak; passage says infiltration is soaking in; distractors are off-topic._

**geo_groundwater [v3] score 2 key OK not sensible H1 H4 H5**: What happens when we dig a well?  
  - Rainwater from rooftops is led into pits or old wells  
  ✅ We usually find water at some depth below the ground  
  - Groundwater is stored in large empty underground swimming pools or rivers  
  - Groundwater is a big underground lake or river  
  _Pure recall of first sentence; distractors are unrelated statements, not misconceptions; key only plain-fit._

**geo_monsoon [v3] score 2 key OK not sensible H4 H5 H6**: What happens when the moist winds are forced to rise over the Western Ghats?  
  - Moist winds from the ocean begin to move towards the land  
  - Winds blow directly from high to low pressure in a straight line  
  ✅ They cool and drop heavy rain on the western slopes  
  - Jet streams are strong winds that blow near the ground over India  
  _Key copies passage wording; distractors are random passage sentences or off-topic; mostly recall._

**geo_monsoon [v3] score 2 key OK SENSIBLE H1 H6 H4**: Why is India's climate called a monsoon climate?  
  ✅ Because the direction of the winds reverses with the seasons  
  - Because the air over the Indian Ocean is cooler  
  - Because the monsoon arrives in all parts of India on the same date  
  - Because the Tropic of Cancer makes all of India tropical  
  _Key restates passage sentence (recall, 'direction of winds' leaks via 'monsoon'); distractors weak._

**geo_monsoon [v3] score 1 key OK not sensible H2 H3 H4 H7**: Why is the pressure there higher?  
  - Because jet streams are strong winds that blow near the ground over India  
  ✅ Because the air over the Indian Ocean is cooler  
  - Because the eastern side receives much less rain  
  - Because places at higher altitude are hotter  
  _'There' is undefined; question is unanswerable without the passage's context; distractors off-topic._

**geo_monsoon [v3] score 2 key OK not sensible H3 H4 H5 H6**: Why do moist winds from the ocean begin to move towards the land?  
  - Because winds blow directly from high to low pressure in a straight line  
  - Because the land heats up much faster than the sea  
  ✅ Because winds blow from high pressure to low pressure  
  - Because the Coriolis force is what makes air move from high to low pressure  
  _B is also true cause; key restates question; D and A are odd._

**geo_seasons [v3] score 2 key OK SENSIBLE H1 H4 H6**: Why is the Earth called the planet of revolution?  
  - Because the half of the Earth facing the Sun has day  
  ✅ Because it travels around the Sun in a path called its orbit  
  - Because the Earth rotates from East to West  
  - Because the Sun moves around the Earth every day  
  _Recall of the orbit sentence; the 'planet of revolution' premise is invented; the key leaks 'travels around'._

**geo_seasons [v3] score 2 key OK SENSIBLE H1 H4 H6**: Why is February called a leap year?  
  - Because the Northern Hemisphere leans towards the Sun for part of the year  
  ✅ Because every four years the extra hours add up to one whole day  
  - Because a leap year happens every three years  
  - Because a leap year has 365 days and an extra day is dropped  
  _Wrongly says February is a leap year; mostly recall; options C and D are weak._

**geo_seasons [v3] score 2 key OK not sensible H1 H2 H4 H6**: Why do many people believe that summer comes?  
  - Because one full trip takes about 365 days  
  - Because the Sun moves around the Earth every day  
  - Because the Earth rotates from East to West  
  ✅ Because the Earth moves closer to the Sun  
  _Garbled stem; 'comes' is incomplete; distractors B and C are off-topic for summer._

**geo_soils [v3] score 2 key OK not sensible H1 H5 H6**: Why is soil important for agriculture?  
  ✅ Because almost all our food grows in it  
  - Because india has many types of soil  
  - Because laterite soil is fertile and good for most crops  
  - Because alluvial soil is fertile mainly  
  _Pure recall, answer copies passage and repeats question words; distractors off-topic/not reasons._

**geo_soils [v3] score 1 KEY WRONG not sensible H3 H4 H5 H1**: Why is soil important in India?  
  ✅ Because it provides food and sustains the environment over thousands of years  
  - Because laterite soil forms in areas with high temperature  
  - Because laterite soil is fertile and good for most crops  
  - Because bangar soil is more fertile than Khadar soil  
  _Key adds unsupported 'sustains the environment'; distractors are irrelevant or outside the passage._

**geo_soils [v3] score 2 key OK not sensible H1 H4 H6**: Why is laterite soil formed in such areas?  
  - Because soil is formed only from the weathering of rocks  
  - Because laterite soil is fertile and good for most crops  
  - Because alluvial soil is the most widespread  
  ✅ Because of high temperature and heavy rainfall  
  _Key correct but recall; distractors are unrelated facts, not misconceptions; 'such areas' vague._

**geo_soils [v3] score 1 KEY WRONG not sensible H3 H4 H1**: Why do red and yellow soils form on old crystalline rocks?  
  - Because soil is formed only from the weathering of rocks  
  ✅ Because they get their red color from iron  
  - Because almost all our food grows in it  
  - Because arid soil is red or yellow in colour and very rich in humus  
  _Passage doesn't explain why they form on crystalline rocks; iron explains colour, not formation._

**geo_sundarbans_ocr [v3] score 2 key OK not sensible H1 H4 H5 H6**: Why do mangroves have special roots?  
  - Because birds are also found there  
  ✅ Because these roots help plants breathe  
  - Because plants only perform photosynthesis and do not breathe  
  - Because mangroves are only found in the ocean  
  _Key correct, but 'special roots/breathe' leaks answer; distractors A, C, D are off-topic, silly._

**his_1857 [v3] score 1 KEY WRONG not sensible H1 H3 H4 H5 H6**: Why was the revolt of 1857 a challenge to British rule?  
  - Because the cartridges had to be bitten open before use  
  ✅ Because it challenged British rule in India in the nineteenth century  
  - Because bahadur Shah Zafar was a powerful military general who planned the revolt  
  - Because only the sepoys were unhappy with the British  
  _Key restates the question (leak); the passage's reasons (spread, wide participation) appear in no option._

**his_1857 [v3] score 2 key OK not sensible H1 H4 H7**: Why were both Hindu and Muslim soldiers offended?  
  ✅ Because the cartridges had to be bitten open before use  
  - Because local rulers joined the soldiers  
  - Because the revolt happened only  
  - Because bahadur Shah Zafar was a powerful military general who planned the revolt  
  _Key is correct but distractors are off-topic or ungrammatical ('happened only'); the key is recall._

**his_1857 [v3] score 2 key OK not sensible H4 H5**: Why did the British bring in more troops?  
  - Because bahadur Shah Zafar was a powerful military general who planned the revolt  
  ✅ Because the rebels lacked a plan and modern weapons  
  - Because the cartridges had to be bitten open before use  
  - Because only the sepoys were unhappy with the British  
  _Key is correct but the distractors are irrelevant recycled fragments, so it is a giveaway._

**his_ashoka [v3] score 2 key OK not sensible H1 H4 H5**: Why did Ashoka decide not to fight a war of conquest?  
  - Because ashoka's inscriptions were all written in Sanskrit  
  ✅ Because he felt sorrow for the suffering he saw  
  - Because ashoka had his messages carved on rocks  
  - Because kalinga was a small village that Ashoka conquered easily  
  _Key correct but near-verbatim recall; distractors are off-topic passage fragments, obvious._

**his_ashoka [v3] score 1 KEY WRONG not sensible H3 H4 H5**: Why did Ashoka fight a war against Kalinga?  
  - Because kalinga was a small village that Ashoka conquered easily  
  - Because the Sarnath lion capital was a throne where Ashoka sat to give orders  
  - Because the wheel on it appears on our national flag  
  ✅ Because he wanted to conquer Odisha and expand his empire  
  _Passage never states why he fought Kalinga; key D is only a paraphrase of 'conquer Kalinga'._

**his_ashoka [v3] score 1 KEY WRONG not sensible H3 H4 H5 H6**: Why is the wheel on the national flag shown on the pillar?  
  - Because ashoka's inscriptions were all written in Sanskrit  
  - Because began to follow what he called dhamma  
  ✅ Because it forms the national emblem of India today  
  - Because inscriptions were written on paper by the Mauryan kings  
  _Passage gives no reason for wheel; key C is a non sequitur, wheel not emblem._

**his_chola [v3] score 2 key OK not sensible H1 H4 H5**: Why is the Brihadeeswara temple considered one of the largest temples in India?  
  - Because a 'Nadu' was a small neighborhood inside a village  
  ✅ Because its tower rises about 66 metres high  
  - Because chola temples were not only places of worship  
  - Because king Harshavardhana was never defeated  
  _Distractors A and D are off-topic; B is the only on-topic option._

**his_chola [v3] score 2 key OK not sensible H1 H4 H5**: What happens when the clay is heated?  
  ✅ The wax melts  
  - Silk was invented in India  
  - Irrigation in the Chola period happened naturally without human planning  
  - Dance attached to them  
  _Answer is direct recall; distractors B, C, D are unrelated to the question._

**his_dandi [v3] score 2 key OK not sensible H1 H4 H5 H6**: Why did the Salt March show that ordinary people could challenge a powerful empire?  
  ✅ Because they refused to obey an unjust law without using violence  
  - Because gandhi called off the Non-Cooperation movement  
  - Because the 'Quit India' movement was completely non-violent  
  - Because salt is something that every person  
  _Key is the passage's closing sentence echoed; distractors off-topic/irrelevant; leaks 'refusing'._

**his_dandi [v3] score 2 key OK not sensible H3 H4 H5**: Why did Gandhi break the salt law?  
  - Because gandhi called off the Non-Cooperation movement  
  - Because gandhi chose salt for the march  
  ✅ Because he wanted to promote civil disobedience  
  - Because salt is something that every person  
  _C plausible but distractors are junk fragments; only complete on-topic option._

**his_dandi [v3] score 1 KEY WRONG not sensible H3 H4 H5**: Why was salt a centre of India's struggle for freedom?  
  - Because the demand for Pakistan was part of the Congress's plan from the beginning  
  ✅ Because it was the main source of food and money in 1930  
  - Because gandhi chose salt for the march  
  - Because the Salt March showed that ordinary people  
  _Key B is false; passage says salt is taxed and needed, not main food/money source._

**his_harappa [v3] score 2 key OK not sensible H4 H5**: Why did its people build large reservoirs cut into rock to collect rainwater?  
  - Because harappan houses were weak  
  - Because other important cities included Mohenjodaro  
  ✅ Because the region was dry  
  - Because the entire civilization was destroyed by a single big war  
  _Key correct but distractors A, B, D are silly/off-topic; the answer is obvious._

**his_harappa [v3] score 1 key OK not sensible H1 H3 H4 H5 H6**: Why were the cities in the text described as having carefully planned drains?  
  - Because harappan houses were weak  
  ✅ Because they were built with proper drainage systems  
  - Because ancient people didn't care about hygiene  
  - Because many of these cities were divided into two parts  
  _Circular: 'planned drains' answered by 'proper drainage systems'; distractors silly or irrelevant._

**his_harappa [v3] score 2 key OK not sensible H3 H4 H5**: Why do we know much of what we know comes from the remains of buildings, pots, seals, and tools?  
  ✅ Because the Harappan script has not yet been read  
  - Because harappan seals were used  
  - Because we have read many books written by Harappan kings  
  - Because many of these cities were divided into two parts  
  _Key A is plausible, but stem is awkward; distractors are silly/off-topic and obviously wrong._

**his_harappa [v3] score 1 KEY WRONG not sensible H3 H4 H5 H6**: Why is the citadel called the western part?  
  - Because the first site of this civilisation to be discovered  
  ✅ Because it was smaller but higher and is called the citadel  
  - Because all Harappan cities were exactly the same and had only two parts  
  - Because the Citadel was a military fort used for fighting wars  
  _False premise: citadel is western part because...? Passage gives no reason; key just restates description._

**his_mughal [v3] score 1 KEY WRONG not sensible H1 H3 H4 H5 H6**: Why did the mansabdar hold a position in the emperor's service?  
  ✅ Because he was given a rank called zat  
  - Because the Mughal emperors ruled a very large  
  - Because zat rank refers to the number of elephants an officer owned  
  - Because zamindars were Mughal government officials appointed from Delhi  
  _Question is incoherent; A merely restates rank; no option truly explains the position; distractors off-topic._

**his_mughal [v3] score 2 key OK not sensible H4 H5 H6**: Why did Akbar follow the policy of universal peace?  
  - Because sulh-i kul was a new religion that Akbar forced everyone to join  
  - Because a mansabdar was a person who held a mansab  
  ✅ Because it did not discriminate between people of different religions  
  - Because the Mughals were proud to be called Mongols  
  _Key restates 'universal peace' as definition; leaks 'discriminate'; distractors off-topic or silly (Mongols)._

**his_mughal [v3] score 2 key OK not sensible H4 H5 H6**: Why did Akbar organize an effective system of administration?  
  - Because akbar also followed a policy called sulh-i kul  
  - Because zamindars were Mughal government officials appointed from Delhi  
  - Because the Mughal Empire became small and weak during Aurangzeb's reign  
  ✅ Because he needed a system to manage his empire  
  _Correct but the passage's first sentence is nearly copied; distractors off-topic (Aurangzeb, zamindars), and the key is the only plausible one._

**phy_circuit [v3] score 2 key OK not sensible H1 H4 H5 H6**: Why do bulbs in a series circuit go off when one fuses?  
  - Because a circuit is closed  
  ✅ Because the path is broken and all other bulbs go off too  
  - Because a switch is used to open or close this path  
  - Because in a series circuit, the bulb closer to the positive terminal glows brighter  
  _Key restates question; distractors off-topic/irrelevant; D is a false leftover; correct option longest._

**phy_circuit [v3] score 2 key OK not sensible H1 H4 H5**: What happens when the switch is on?  
  - In a series circuit, the bulb closer to the positive terminal glows brighter  
  ✅ The circuit is closed and the bulb glows  
  - A switch stores electricity when it is in the OFF position  
  - The longer line stands for the positive terminal  
  _Plain recall; distractors are unrelated passage facts or invented; key is longest._

**phy_circuit [v3] score 2 key OK not sensible H1 H4 H5 H6**: Why are the lights and fans in parallel connected?  
  - Because all wires get equally hot when the same current flows through them  
  - Because bulbs can also be joined one after another in a single path  
  ✅ Because each one can be switched on or off without affecting the others  
  - Because in a series circuit, the bulb closer to the positive terminal glows brighter  
  _Near-verbatim recall; distractors unrelated or invented; 'each one' leaks; key longest._

**phy_circuit [v3] score 1 KEY WRONG not sensible H1 H3 H4 H5**: Why is a simple electric circuit important?  
  ✅ Because it allows current to flow and create electricity  
  - Because conventional current flows from positive to negative  
  - Because electric current is consumed or used up by the bulb in a circuit  
  - Because the longer line stands for the positive terminal  
  _Vague question; 'create electricity' is wrong, passage doesn't support any option._

**phy_friction [v3] score 2 key OK not sensible H1 H4 H5 H6**: What happens when two surfaces press together?  
  - Ball bearings are fitted in the wheels of cycles  
  ✅ These bumps lock into each other, and this interlocking resists sliding  
  - A larger surface area in contact creates more friction  
  - Friction only acts on objects that are already moving  
  _Recall of a passage sentence; B copies the passage and is longest; distractors off-topic._

**phy_friction [v3] score 1 key OK not sensible H1 H3 H4 H5**: What happens when you push a heavy box across the floor?  
  - Friction only acts on objects that are already moving  
  ✅ It does not slide forever  
  - A car could not stop  
  - A larger surface area in contact creates more friction  
  _Passage says box slows and stops; 'does not slide forever' is a fragment, distractors irrelevant._

**phy_friction [v3] score 2 key OK not sensible H1 H4 H5**: What happens when you rub your palms together quickly?  
  - A car could not stop  
  - A larger surface area in contact creates more friction  
  ✅ They become warm  
  - Friction only produces heat when you rub things very fast  
  _Pure recall; D is a near-giveaway paraphrase; other options off-topic and irrelevant._

**phy_friction [v3] score 3 key OK not sensible H4 H5 H6**: Why are oil and grease placed between the moving parts of machines and ball bearings fitted in the wheels of cycles?  
  ✅ Because rolling causes much less friction than sliding  
  - Because our shoes would slip on the ground  
  - Because friction always acts in the opposite direction of the object's motion  
  - Because rolling friction is zero  
  _Reasonable why-question, but A copies passage and is only one; D is implausible._

**phy_magnets [v3] score 2 key OK not sensible H1 H4 H5 H6**: What happens when a bar magnet is hung freely from a thread?  
  - A magnet's power gets used up over time like a battery  
  ✅ It always comes to rest pointing in the north-south direction  
  - The center of a bar magnet is the strongest part  
  - Materials that are attracted by a magnet are called magnetic materials  
  _Plain recall; key copies passage; distractors off-topic or passage sentences; 'pointing' leak-ish._

**phy_magnets [v3] score 2 key OK not sensible H1 H4 H5**: What happens when two magnets are brought close?  
  - A magnet's power gets used up over time like a battery  
  ✅ Like poles repel each other and unlike poles attract each other  
  - Materials that are attracted by a magnet are called magnetic materials  
  - Electricity and magnetism are the same thing  
  _Recall; key longest and passage-copied; distractors silly/unrelated, repeated across questions._

**phy_magnets [v3] score 2 key OK SENSIBLE H1 H4 H6**: Why are some materials called magnetic materials?  
  ✅ Because they are attracted by a magnet  
  - Because the attraction is strongest near the poles  
  - Because all metals are attracted to magnets  
  - Because electricity and magnetism are the same thing  
  _Circular definition recall; question words leak key; weak distractors._

**phy_mirror [v3] score 2 key OK not sensible H1 H4 H5 H7**: What happens when light falls on a smooth, shiny surface such as a mirror?  
  ✅ It bounces back  
  - 4 metres away from you  
  - Light can bend around corners like sound does  
  - If you walk away from a plane mirror, your image gets smaller  
  _Plain recall; distractors off-topic/irrelevant to question; correct option only fitting answer._

**phy_mirror [v3] score 1 key OK not sensible H4 H5 H6 H3**: Why is the word AMBULANCE written in reverse on the front of ambulances?  
  ✅ Because the image is laterally inverted  
  - Because 4 metres away from you  
  - Because lateral inversion means the image is upside down  
  - Because the image in a pinhole camera is upright  
  _Option B nonsensical, C/D silly; A leaks 'inverted'; only grammatical fit._

**phy_mirror [v3] score 1 key OK not sensible H1 H4 H5 H6**: What happens when you stand 2 metres in front of a mirror?  
  - A mirror image is just a person standing behind a transparent glass  
  ✅ Your image seems to be 2 metres behind it  
  - The ray that bounces back is called the reflected ray  
  - If you walk away from a plane mirror, your image gets smaller  
  _Recall; leaks '2 metres'; distractors irrelevant to question; B only on-topic option._

**phy_pressure [v3] score 1 key OK not sensible H1 H2 H3 H4 H5 H6 H7**: Why does the same force spread over a larger area and the pressure is less?  
  - Because pressure and Force are exactly the same thing  
  - Because a larger area always results in more pressure  
  - Because the pressure on the head is reduced  
  ✅ Because a blunt knife has a wider edge  
  _Question is circular and ungrammatical; D restates the passage, and the wrong options are off-topic fragments._

**phy_pressure [v3] score 1 key OK not sensible H1 H4 H5 H6**: What happens when the same force acts on a smaller area?  
  - A larger area always results in more pressure  
  - Pins have pointed tips  
  ✅ The pressure is greater  
  - Pressure and Force are exactly the same thing  
  _Answer copies the question's wording; distractors are off-topic recycled fragments; the question is recall._

**phy_pressure [v3] score 1 key OK not sensible H1 H4 H6 H7**: Why does the force from Grandfather's hand produce a large pressure and the knife cut through a tomato easily?  
  ✅ Because the sharp edge of a knife has a very small area  
  - Because force is something an object 'has' or 'contains' like an ingredient  
  - Because pressure and Force are exactly the same thing  
  - Because meena watched her grandfather cut vegetables in the kitchen  
  _Answer repeats the passage's cause; option D is a silly sentence copied from the text; the question is too long._

**phy_pressure [v3] score 1 key OK not sensible H1 H4 H5 H6**: Why is the pressure on the head reduced and the load easier to carry?  
  - Because the force from Grandfather's hand produces a large pressure  
  ✅ Because the cloth increases the area of contact  
  - Because a larger area always results in more pressure  
  - Because pressure and Force are exactly the same thing  
  _Recall dressed up as 'why'; recycled distractors; D is the only one that fits the cloth context._

**phy_sound [v3] score 2 key OK not sensible H1 H3 H4 H5 H6**: Why do we hear different types of sounds?  
  - Because dolphins can hear ultrasonic sounds  
  ✅ Because different frequencies are heard, like a whistle and a drum  
  - Because high-pitched sounds are always louder than low-pitched sounds  
  - Because loudness is determined by how fast the source is vibrating  
  _Vague; B restates 'different frequencies'; distractors off-topic and not passage-based; longest, leaks key words._

**phy_sound [v3] score 2 key OK not sensible H1 H4 H5 H6**: What happens when you pluck the string of a sitar?  
  - Loudness is determined by how fast an object vibrates  
  - Sound travels faster in solids than in air  
  ✅ The string vibrates and you hear a sound  
  - Air particles travel from the speaker's mouth to the listener's ear  
  _Pure recall; distractors are unrelated passage statements; C is only on-topic option; leaks 'string vibrates'._

**phy_sound [v3] score 2 key OK not sensible H1 H4 H5 H6**: What happens when you put your ear to one end of a long table and a friend taps the other end gently?  
  - Air particles travel from the speaker's mouth to the listener's ear  
  - Sounds below this range are called infrasonic  
  ✅ You hear the tap clearly through the wood  
  - Humans can hear ultrasound if it is played at a very high volume  
  _Recall of the table example; distractors unrelated to question; correct option copies the passage wording._

**phy_sound [v3] score 2 key OK not sensible H1 H3 H4**: Why do we hear sound?  
  - Because sound is a physical substance that flows through the air like a gas  
  ✅ Because sound needs a medium to travel  
  - Because sound travels faster in air than in solids  
  - Because a low frequency gives a low-pitched sound  
  _Ambiguous question; vibration is the passage's cause of sound, medium only enables travel; key arguably wrong._
