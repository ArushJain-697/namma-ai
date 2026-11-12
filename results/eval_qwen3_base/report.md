# Batch evaluation: executorch:qwen3-0.6b-8da4w

- passages: 40 (errors 0); with at least 3 questions shown: 40
- questions shown: 122 = 49 written by the model + 73 fill-in-the-blank by code (model share 40%)
- model-drafted questions accepted: 49 of 236 (21%)
- summary sentences: {'model rewrite': 94, 'kept original': 2}
- why questions were held back: {'stem_no_answer_leak': 119, 'stem_answers_to_key': 44, 'stem_question_mark': 44, 'stem_in_passage': 25, 'stem_not_echo': 19, 'stem_readability': 8, 'stem_length': 5}
- 19.1 s per passage on this machine, 1076 model calls in all

Rate the shown questions in rating.csv (good / ok / bad). ✅ marks the answer key.

## phy_friction
*subject physics, class 8, style cause-effect* · OK: 227 words · 19.0 s

**Summary**
- [model rewrite] A rough surface like a brick floor has more bumps, so it makes more friction than a smooth marble floor.
- [model rewrite] The harder the two surfaces are pressed together, the more friction they have.

**Shown to the student: 3**  (0 written by the model, 3 fill-in-the-blank by code)

1. **Fill in the blank: Friction is not always a _____.**  _(code fill-in-the-blank, from sentence 9)_
   - A) forever
   - B) touch
   - C) slide
   - D) nuisance  ✅
   - source: "Friction is not always a nuisance."
2. **Fill in the blank: Sometimes we want to _____ friction.**  _(code fill-in-the-blank, from sentence 13)_
   - A) reduce  ✅
   - B) slide
   - C) force
   - D) floor
   - source: "Sometimes we want to reduce friction."
3. **Fill in the blank: It slows down and stops because of _____.**  _(code fill-in-the-blank, from sentence 2)_
   - A) floor
   - B) friction  ✅
   - C) forever
   - D) slide
   - source: "It slows down and stops because of friction."

**Held back: 6**

- RED, answer **floor**, sentence 6: "A rough surface such as a brick floor has larger bumps, so it produces more friction than a polished marble floor."
  - draft "What type of surface produces more friction than a polished marble floor?"  [stem_no_answer_leak]
  - draft "What is the friction on a rough surface compared to a polished surface?"  [stem_answers_to_key]  → answered back: "more"
  - draft "What is the term for a rough surface that produces more friction?"  [stem_answers_to_key]  → answered back: "friction"
- RED, answer **surfaces**, sentence 3: "Friction is a force that acts between two surfaces that touch each other, and it always acts against the direction of motion."
  - draft "What is the force that acts between two surfaces that touch each other?"  [stem_no_answer_leak]
  - draft "What is the force that acts between two surfaces that touch each other?"  [stem_no_answer_leak]
  - draft "What is a force that acts between two surfaces that touch each other?"  [stem_no_answer_leak]
- RED, answer **sliding**, sentence 14: "Oil and grease are put between the moving parts of machines, and ball bearings are fitted in the wheels of cycles, because rolling causes much less friction than sliding."
  - draft "Because rolling causes less friction than sliding."  [stem_question_mark, stem_no_answer_leak]
  - draft "Because rolling causes less friction than sliding."  [stem_question_mark, stem_no_answer_leak]
  - draft "Because rolling causes much less friction than sliding, what do we do?"  [stem_no_answer_leak]
- RED, answer **shoes**, sentence 15: "On the other hand, the treads on tyres and the grooves on the soles of sports shoes are designed to increase friction and give a better grip."
  - draft "What is designed to increase friction and give a better grip?"  [stem_answers_to_key]  → answered back: "treads and grooves"
  - draft "What is designed to increase friction and give a better grip?"  [stem_answers_to_key]  → answered back: "treads and grooves"
  - draft "What are designed to increase friction and give a better grip?"  [stem_answers_to_key]  → answered back: "treads on tyres and the grooves on the soles of sports shoes"
- RED, answer **bumps**, sentence 4: "Even surfaces that look smooth have tiny bumps and hollows."
  - draft "What are the bumps and hollows called?"  [stem_no_answer_leak]
  - draft "What are the bumps in the surfaces?"  [stem_no_answer_leak]
  - draft "What are the bumps and hollows called?"  [stem_no_answer_leak]
- RED, answer **push**, sentence 8: "That is why a box full of books is harder to push than an empty one."
  - draft "What is the reason that a box full of books is harder to push than an empty one?"  [stem_no_answer_leak, stem_not_echo]
  - draft "What is the reason that a box full of books is harder to push than an empty one?"  [stem_no_answer_leak, stem_not_echo]
  - draft "What is harder to push?"  [stem_no_answer_leak]

## phy_circuit
*subject physics, class 7, style process* · OK: 232 words · 18.5 s

**Summary**
- [model rewrite] A simple electric circuit needs a power source like a cell, a light that uses electricity, and connecting wires to make a complete path.
- [kept original (rewrite failed checks)] In a series circuit the same current passes through every bulb, and the current is not used up on the way: just as much current returns to the cell as leaves it.

**Shown to the student: 3**  (0 written by the model, 3 fill-in-the-blank by code)

1. **Fill in the blank: They are joined in parallel, so that each one can be _____ on or off without affecting the others.**  _(code fill-in-the-blank, from sentence 15)_
   - A) bulb
   - B) circuit
   - C) switched  ✅
   - D) closed
   - source: "They are joined in parallel, so that each one can be switched on or off without affecting the others."
2. **Fill in the blank: A simple electric circuit needs three things: a source of electricity such as a cell, a device that uses electricity such as a bulb, and connecting wires that make a complete _____.**  _(code fill-in-the-blank, from sentence 1)_
   - A) gap
   - B) positive
   - C) path  ✅
   - D) negative
   - source: "A simple electric circuit needs three things: a source of electricity such as a cell, a device that uses electricity such as a bulb, and connecting wires that make a complete path."
3. **Fill in the blank: In a series circuit the same current passes through every bulb, and the current is not used up on the way: just as much current returns to the _____ as leaves it.**  _(code fill-in-the-blank, from sentence 12)_
   - A) positive
   - B) cell  ✅
   - C) device
   - D) negative
   - source: "In a series circuit the same current passes through every bulb, and the current is not used up on the way: just as much current returns to the cell as leaves it."

**Held back: 6**

- RED, answer **path**, sentence 1: "A simple electric circuit needs three things: a source of electricity such as a cell, a device that uses electricity such as a bulb, and connecting wires that make a complete path."
  - draft "What is the complete path that a simple electric circuit needs?"  [stem_no_answer_leak]
  - draft "What is the complete path that a simple electric circuit needs?"  [stem_no_answer_leak]
  - draft "What is the complete path that a simple electric circuit needs?"  [stem_no_answer_leak]
- RED, answer **cell**, sentence 12: "In a series circuit the same current passes through every bulb, and the current is not used up on the way: just as much current returns to the cell as leaves it."
  - draft "The current is returned to the cell as much as it leaves it."  [stem_question_mark, stem_no_answer_leak]
  - draft "The current is returned to the cell as much as it leaves it."  [stem_question_mark, stem_no_answer_leak]
  - draft "The current is not used up on the way, just as much as it returns to the cell."  [stem_question_mark, stem_no_answer_leak]
- RED, answer **closed**, sentence 4: "When the switch is on, the circuit is closed and the bulb glows."
  - draft "When the switch is on, the circuit is closed and the bulb glows."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "When the switch is on, the circuit is closed and the bulb glows."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "When the switch is on, the circuit is closed and the bulb glows."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
- RED, answer **terminal**, sentence 6: "A cell has two terminals, a positive terminal and a negative terminal."
  - draft "What are the two terminals in a cell?"  [stem_answers_to_key]  → answered back: "positive and negative"
  - draft "What is a terminal in a cell?"  [stem_no_answer_leak]
  - draft "What are the terminals in a cell?"  [stem_answers_to_key]  → answered back: "positive and negative"
- RED, answer **series**, sentence 14: "In our homes, lights and fans are not joined in series."
  - draft "In our homes, lights and fans are not joined in series."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "In our homes, lights and fans are not joined in series."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "In our homes, the lights and fans are not joined in series."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
- AMBER, answer **current**, sentence 5: "When it is off, there is a gap in the path and the current stops."
  - draft "What happens when the current stops?"  [stem_no_answer_leak]
  - draft "What happens when it is off?"  [stem_in_passage]  → answered back: "current stops"
  - draft "What happens when the current is off?"  [stem_no_answer_leak, stem_in_passage]
  - options: cell | electric | current | circuit

## phy_sound
*subject physics, class 8, style definitions* · OK: 222 words · 19.6 s

**Summary**
- [model rewrite] Sound is made when an object vibrates.
- [model rewrite] Sound travels faster in solids than in air.
- [model rewrite] The human ear can hear sounds with frequencies from 20 to 20,000 hertz.

**Shown to the student: 3**  (2 written by the model, 1 fill-in-the-blank by code)

1. **What is the range of frequencies that the human ear can hear?**  _(model, from sentence 14)_
   - A) hertz  ✅
   - B) motion
   - C) to-and-fro
   - D) vibration
   - source: "The human ear can hear sounds with frequencies from about 20 hertz to 20,000 hertz."
2. **What does sound travel faster in?**  _(model, from sentence 10)_
   - A) vibrates
   - B) beings
   - C) solids  ✅
   - D) astronauts
   - source: "Sound travels faster in solids than in air."
3. **Fill in the blank: In human beings, sound is _____ by the voice box, called the larynx, at the upper end of the windpipe.**  _(code fill-in-the-blank, from sentence 5)_
   - A) travel
   - B) vibration
   - C) high-pitched
   - D) produced  ✅
   - source: "In human beings, sound is produced by the voice box, called the larynx, at the upper end of the windpipe."

**Held back: 4**

- RED, answer **vibrates**, sentence 1: "Sound is produced when an object vibrates."
  - draft "What is produced when an object vibrates?"  [stem_no_answer_leak, stem_not_echo]
  - draft "What is produced when an object vibrates?"  [stem_no_answer_leak, stem_not_echo]
  - draft "What is produced when an object vibrates?"  [stem_no_answer_leak, stem_not_echo]
- AMBER, answer **ultrasonic**, sentence 15: "Sounds below this range are called infrasonic, and sounds above it are called ultrasonic."
  - draft "What are the types of sound waves?"  [stem_in_passage]  → answered back: "infrasonic and ultrasonic"
  - draft "What are the types of sound waves?"  [stem_in_passage]  → answered back: "infrasonic and ultrasonic"
  - draft "What kind of sound is below a certain range?"  [stem_in_passage, stem_answers_to_key]  → answered back: "infrasonic"
  - options: travel | hertz | ultrasonic | rapid
- RED, answer **travel**, sentence 7: "Sound needs a medium to travel."
  - draft "What is the medium that sound needs to travel?"  [stem_no_answer_leak]
  - draft "What is the medium used for sound?"  [stem_answers_to_key]  → answered back: "medium"
  - draft "What is needed for sound to travel?"  [stem_no_answer_leak]
- RED, answer **frequency**, sentence 13: "A high frequency gives a high-pitched sound, like a whistle, while a low frequency gives a low-pitched sound, like a drum."
  - draft "What is the characteristic of sound based on its frequency?"  [stem_no_answer_leak, stem_in_passage]
  - draft "What is the name of the sound produced by a high frequency?"  [stem_no_answer_leak]
  - draft "What gives a high-pitched sound like a whistle and a low-pitched sound like a drum?"  [stem_answers_to_key]  → answered back: "sound"

## phy_mirror
*subject physics, class 8, style law-with-numbers* · OK: 250 words · 18.1 s

**Summary**
- [model rewrite] The angle between the incident ray and the normal is called the angle of incidence, and the angle between the reflected ray and the normal is called the angle of reflection.
- [model rewrite] If a ray hits a mirror at 30 degrees, it will reflect at 30 degrees.

**Shown to the student: 3**  (1 written by the model, 2 fill-in-the-blank by code)

1. **What is the angle of incidence in the sentence?**  _(model, from sentence 8)_
   - A) hits
   - B) front
   - C) incident
   - D) degrees  ✅
   - source: "So if a ray strikes a mirror at an angle of incidence of 30 degrees, it will be reflected at 30 degrees."
2. **Fill in the blank: When light falls on a smooth, shiny surface such as a mirror, it _____ back.**  _(code fill-in-the-blank, from sentence 1)_
   - A) degrees
   - B) ambulances
   - C) image
   - D) bounces  ✅
   - source: "When light falls on a smooth, shiny surface such as a mirror, it bounces back."
3. **Fill in the blank: The image appears as far behind the mirror as the object is in _____ of it.**  _(code fill-in-the-blank, from sentence 11)_
   - A) reflection
   - B) plane
   - C) front  ✅
   - D) ray
   - source: "The image appears as far behind the mirror as the object is in front of it."

**Held back: 5**

- RED, answer **reflection**, sentence 6: "The angle between the incident ray and the normal is the angle of incidence, and the angle between the reflected ray and the normal is the angle of reflection."
  - draft "What is the angle between the incident ray and the normal?"  [stem_answers_to_key]  → answered back: "one"
  - draft "What is the angle between the incident ray and the normal?"  [stem_answers_to_key]  → answered back: "one"
  - draft "What is the term for the angle between the incident ray and the normal?"  [stem_answers_to_key]  → answered back: "angle of incidence"
- RED, answer **reflected**, sentence 3: "The ray of light that falls on the mirror is called the incident ray, and the ray that bounces back is called the reflected ray."
  - draft "What is called the incident ray?"  [stem_answers_to_key]  → answered back: "incident ray"
  - draft "What is called the incident ray?"  [stem_answers_to_key]  → answered back: "incident ray"
  - draft "What is called the reflected ray?"  [stem_no_answer_leak]
- RED, answer **plane**, sentence 9: "The second law says that the incident ray, the normal and the reflected ray all lie in the same plane."
  - draft "What is the plane in which all incident rays, normal rays, and reflected rays lie?"  [stem_no_answer_leak]
  - draft "What plane contains incident rays, normal rays, and reflected rays?"  [stem_no_answer_leak]
  - draft "What is the plane?"  [stem_no_answer_leak]
- RED, answer **image**, sentence 13: "The image is also laterally inverted, which means that your left hand appears as the right hand of the image."
  - draft "What does the image mean?"  [stem_no_answer_leak]
  - draft "What does the image appear as?"  [stem_no_answer_leak]
  - draft "What does the image mean?"  [stem_no_answer_leak]
- RED, answer **object**, sentence 10: "A plane mirror forms an image that is upright and of the same size as the object."
  - draft "What is the image formed by a plane mirror?"  [stem_answers_to_key]  → answered back: "upright"
  - draft "What is formed by a plane mirror?"  [stem_answers_to_key]  → answered back: "images"
  - draft "What is the result of a plane mirror forming an image?"  [stem_answers_to_key]  → answered back: "upright and virtual"

## phy_magnets
*subject physics, class 6, style list-short* · OK: 163 words · 16.6 s

**Summary**
- [model rewrite] Every magnet has two poles, one north and one south.
- [model rewrite] When two magnets with the same pole repel each other, and two magnets with opposite poles attract each other.
- [model rewrite] To keep them safe, bar magnets are stored in pairs with their unlike poles on the same side, separated by a piece of wood.

**Shown to the student: 3**  (1 written by the model, 2 fill-in-the-blank by code)

1. **What do magnets have?**  _(model, from sentence 3)_
   - A) direction
   - B) nickel
   - C) pole  ✅
   - D) attract
   - source: "Every magnet has two poles, a north pole and a south pole."
2. **Fill in the blank: To keep them safe, bar magnets are stored in pairs with their unlike poles on the same side, separated by a piece of _____.**  _(code fill-in-the-blank, from sentence 10)_
   - A) direction
   - B) magnetic
   - C) wood  ✅
   - D) attract
   - source: "To keep them safe, bar magnets are stored in pairs with their unlike poles on the same side, separated by a piece of wood."
3. **Fill in the blank: When two magnets are brought close, like poles repel each other and unlike poles _____ each other.**  _(code fill-in-the-blank, from sentence 7)_
   - A) iron
   - B) attract  ✅
   - C) piece
   - D) wood
   - source: "When two magnets are brought close, like poles repel each other and unlike poles attract each other."

**Held back: 4**

- RED, answer **wood**, sentence 10: "To keep them safe, bar magnets are stored in pairs with their unlike poles on the same side, separated by a piece of wood."
  - draft "What is stored in pairs with their unlike poles on the same side, separated by a piece of wood?"  [stem_no_answer_leak]
  - draft "What is stored in pairs with their unlike poles on the same side, separated by a piece of wood?"  [stem_no_answer_leak]
  - draft "What is used to keep them safe?"  [stem_answers_to_key]  → answered back: "bar magnets"
- RED, answer **attract**, sentence 7: "When two magnets are brought close, like poles repel each other and unlike poles attract each other."
  - draft "When two magnets are brought close, like poles attract each other and unlike poles repel each other."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "When two magnets are brought close, like poles attract each other and unlike poles repel each other."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "When two magnets are brought close, like poles repel each other and unlike poles attract each other, what happens?"  [stem_no_answer_leak, stem_not_echo, stem_readability]
- RED, answer **direction**, sentence 5: "If a bar magnet is hung freely from a thread, it always comes to rest pointing in the north-south direction."
  - draft "What direction does a bar magnet always point when hung freely?"  [stem_no_answer_leak]
  - draft "What is the direction in which the bar magnet always points?"  [stem_no_answer_leak]
  - draft "What is the direction in which a bar magnet always points?"  [stem_no_answer_leak]
- RED, answer **dropped**, sentence 9: "Magnets lose their magnetism if they are heated, hammered or dropped often."
  - draft "What happens to magnets when they are dropped?"  [stem_no_answer_leak]
  - draft "What happens to magnets when they are dropped?"  [stem_no_answer_leak]
  - draft "What happens to magnets when they are dropped?"  [stem_no_answer_leak]

## phy_pressure
*subject physics, class 8, style story* · OK: 234 words · 18.1 s

**Summary**
- [model rewrite] The knife cuts through a tomato with a lot of pressure from Grandfather's hand.
- [model rewrite] A blunt knife has a wider edge, so the same force spreads over a larger area, and the pressure is less.

**Shown to the student: 3**  (1 written by the model, 2 fill-in-the-blank by code)

1. **What happens with depth in water?**  _(model, from sentence 16)_
   - A) porters
   - B) spreads
   - C) vegetables
   - D) increases  ✅
   - source: "Water presses on the walls of its container, and the pressure increases with depth."
2. **Fill in the blank: He sharpened his _____ on a stone before he began.**  _(code fill-in-the-blank, from sentence 2)_
   - A) force
   - B) knife  ✅
   - C) easily
   - D) pressure
   - source: "He sharpened his knife on a stone before he began."
3. **Fill in the blank: That is why the _____ of a dam are made much thicker at the bottom than at the top.**  _(code fill-in-the-blank, from sentence 17)_
   - A) increases
   - B) vegetables
   - C) walls  ✅
   - D) straps
   - source: "That is why the walls of a dam are made much thicker at the bottom than at the top."

**Held back: 5**

- RED, answer **Grandfather's**, sentence 8: "The sharp edge of a knife has a very small area, so the force from Grandfather's hand produces a large pressure and the knife cuts through a tomato easily."
  - draft "The force from Grandfather's hand produces a large pressure and the knife cuts through a tomato easily."  [stem_question_mark, stem_no_answer_leak]
  - draft "The force from Grandfather's hand produces a large pressure and the knife cuts through a tomato easily."  [stem_question_mark, stem_no_answer_leak]
  - draft "The force from Grandfather's hand produces a large pressure and the knife cuts through a tomato easily."  [stem_question_mark, stem_no_answer_leak]
- RED, answer **load**, sentence 12: "The cloth increases the area of contact, so the pressure on the head is reduced and the load is easier to carry."
  - draft "The load is easier to carry."  [stem_question_mark, stem_no_answer_leak]
  - draft "The answer is load."  [stem_question_mark, stem_no_answer_leak, stem_in_passage]
  - draft "The load is easier to carry."  [stem_question_mark, stem_no_answer_leak]
- RED, answer **Meena**, sentence 10: "The same idea explains many things Meena had seen."
  - draft "What does Meena explain?"  [stem_no_answer_leak]
  - draft "What does Meena explain?"  [stem_no_answer_leak]
  - draft "What idea does Meena explain?"  [stem_no_answer_leak]
- RED, answer **force**, sentence 9: "A blunt knife has a wider edge, so the same force spreads over a larger area and the pressure is less."
  - draft "What is the force that spreads over a larger area?"  [stem_no_answer_leak]
  - draft "What is the force that spreads over a larger area?"  [stem_no_answer_leak]
  - draft "What is the name of the force?"  [stem_no_answer_leak, stem_in_passage]
- RED, answer **easily**, sentence 4: "'A sharp knife cuts easily,' he said."
  - draft "What does he say?"  [stem_in_passage, stem_answers_to_key]  → answered back: "he said that a sharp knife cuts easily."
  - draft "What does the sentence "A sharp knife cuts easily" imply?"  [stem_no_answer_leak]
  - draft "What does he say? easily"  [stem_question_mark, stem_no_answer_leak, stem_in_passage]

## chem_acids
*subject chemistry, class 7, style definitions-examples* · OK: 220 words · 21.1 s

**Summary**
- [model rewrite] When an indicator changes color, it changes when it is added to an acid or a base.
- [model rewrite] Blue litmus paper turns red when you put it in an acid, and red litmus paper turns blue when you put it in a base.

**Shown to the student: 3**  (0 written by the model, 3 fill-in-the-blank by code)

1. **Fill in the blank: _____ is useful in daily life.**  _(code fill-in-the-blank, from sentence 13)_
   - A) Neutralisation  ✅
   - B) turmeric
   - C) soda
   - D) taste
   - source: "Neutralisation is useful in daily life."
2. **Fill in the blank: When an acid is mixed with a base, they cancel each _____ effect.**  _(code fill-in-the-blank, from sentence 11)_
   - A) other's  ✅
   - B) bases
   - C) petals
   - D) lichens
   - source: "When an acid is mixed with a base, they cancel each other's effect."
3. **Fill in the blank: China rose petals give a solution that turns dark pink in an acid and _____ in a base.**  _(code fill-in-the-blank, from sentence 10)_
   - A) green  ✅
   - B) paper
   - C) soda
   - D) taste
   - source: "China rose petals give a solution that turns dark pink in an acid and green in a base."

**Held back: 6**

- RED, answer **contain**, sentence 1: "Some foods taste sour because they contain acids."
  - draft "What do foods contain that make them taste sour?"  [stem_no_answer_leak]
  - draft "What do foods contain that make them taste sour?"  [stem_no_answer_leak]
  - draft "What do acids contain in foods?"  [stem_no_answer_leak]
- RED, answer **litmus**, sentence 7: "Blue litmus paper turns red in an acid, while red litmus paper turns blue in a base."
  - draft "What does the litmus test show?"  [stem_no_answer_leak]
  - draft "What happens to the litmus paper when it's in an acid?"  [stem_no_answer_leak]
  - draft "What color does litmus turn in an acid?"  [stem_no_answer_leak]
- RED, answer **indicator**, sentence 5: "An indicator changes its colour when it is added to an acid or a base."
  - draft "What changes when an indicator is added to an acid or a base?"  [stem_no_answer_leak]
  - draft "What changes when an indicator is added to an acid or a base?"  [stem_no_answer_leak]
  - draft "What changes its colour when it is added to an acid or a base?"  [stem_not_echo]
- RED, answer **soda**, sentence 14: "An ant bite injects formic acid into the skin, and the pain can be relieved by rubbing on a mild base such as moist baking soda."
  - draft "The base used to relieve the pain is called soda."  [stem_question_mark, stem_no_answer_leak]
  - draft "The base used for the pain relief is called soda."  [stem_question_mark, stem_no_answer_leak]
  - draft "The mild base used to relieve the ant bite pain is called soda."  [stem_question_mark, stem_no_answer_leak]
- RED, answer **water**, sentence 9: "A turmeric stain on a white cloth turns red when soap, which is a base, is rubbed on it, and it turns yellow again when washed with plenty of water."
  - draft "What is the process that turns a turmeric stain red when soap is rubbed on it?"  [stem_answers_to_key]  → answered back: "rubbing with soap"
  - draft "What is the process that turns a turmeric stain red when rubbed with soap?"  [stem_answers_to_key]  → answered back: "rubbing with soap"
  - draft "What does the turmeric stain turn into when soap is rubbed on it?"  [stem_answers_to_key]  → answered back: "red and yellow"
- RED, answer **Indian**, sentence 8: "Turmeric is another natural indicator found in every Indian kitchen."
  - draft "Which is a natural indicator found in every Indian kitchen?"  [stem_no_answer_leak, stem_not_echo]
  - draft "Which is the natural indicator found in every Indian kitchen?"  [stem_no_answer_leak, stem_not_echo]
  - draft "Which country is located in the tropical region?"  [stem_in_passage, stem_answers_to_key]  → answered back: "India"

## chem_changes
*subject chemistry, class 7, style compare-examples* · OK: 229 words · 22.8 s

**Summary**
- [model rewrite] In a physical change, a substance changes shape, size, or state, but no new substance is formed.
- [model rewrite] In a chemical change, new substances are formed.
- [model rewrite] The wax burns in the flame to make carbon dioxide, water vapor, heat, and light — that's a chemical change.

**Shown to the student: 3**  (0 written by the model, 3 fill-in-the-blank by code)

1. **Fill in the blank: When ice melts into _____, it is still _____.**  _(code fill-in-the-blank, from sentence 3)_
   - A) paper
   - B) water  ✅
   - C) heat
   - D) dioxide
   - source: "When ice melts into water, it is still water."
2. **Fill in the blank: Changes around us can be _____ into two kinds.**  _(code fill-in-the-blank, from sentence 1)_
   - A) produced
   - B) grouped  ✅
   - C) substance
   - D) reversed
   - source: "Changes around us can be grouped into two kinds."
3. **Fill in the blank: Some processes _____ both kinds of change.**  _(code fill-in-the-blank, from sentence 11)_
   - A) involve  ✅
   - B) water
   - C) paper
   - D) substance
   - source: "Some processes involve both kinds of change."

**Held back: 6**

- RED, answer **chemical**, sentence 13: "The wax vapour then burns in the flame to produce carbon dioxide, water vapour, heat and light, which is a chemical change."
  - draft "What is a chemical change?"  [stem_no_answer_leak]
  - draft "What is a chemical change?"  [stem_no_answer_leak]
  - draft "What is a chemical change?"  [stem_no_answer_leak]
- RED, answer **substance**, sentence 2: "In a physical change, a substance changes its shape, size or state, but no new substance is formed."
  - draft "What is a physical change?"  [stem_answers_to_key]  → answered back: "a physical change"
  - draft "What is a physical change?"  [stem_answers_to_key]  → answered back: "a physical change"
  - draft "What is a physical change?"  [stem_answers_to_key]  → answered back: "a physical change"
- RED, answer **ice**, sentence 5: "Many physical changes can be reversed: water can be frozen back into ice."
  - draft "What can be reversed? ice"  [stem_question_mark, stem_no_answer_leak]
  - draft "What can be reversed? ice"  [stem_question_mark, stem_no_answer_leak]
  - draft "What can be reversed? ice"  [stem_question_mark, stem_no_answer_leak]
- RED, answer **physical**, sentence 14: "Crystallisation, in which pure crystals of a substance such as copper sulphate are obtained from its solution, is a physical change."
  - draft "What is a physical change?"  [stem_no_answer_leak]
  - draft "What is a physical change?"  [stem_no_answer_leak]
  - draft "What is a physical change?"  [stem_no_answer_leak]
- RED, answer **gas**, sentence 9: "A chemical change is often shown by signs such as the release of heat or light, a change in colour, the production of a gas, or a change in smell."
  - draft "What is shown by a chemical change? gas"  [stem_question_mark, stem_no_answer_leak]
  - draft "What is shown by a chemical change? gas"  [stem_question_mark, stem_no_answer_leak]
  - draft "What is shown as a sign of a chemical change? gas"  [stem_question_mark, stem_no_answer_leak]
- RED, answer **paper**, sentence 4: "When a sheet of paper is cut into pieces, each piece is still paper."
  - draft "What remains after cutting a sheet of paper into pieces?"  [stem_no_answer_leak]
  - draft "What remains after cutting a sheet of paper into pieces?"  [stem_no_answer_leak]
  - draft "What remains of the paper after it is cut into pieces?"  [stem_no_answer_leak]

## chem_separation
*subject chemistry, class 6, style process-indian-context* · OK: 222 words · 16.1 s

**Summary**
- [model rewrite] Along the coasts of Gujarat and Tamil Nadu, we get a lot of common salt from sea water.
- [model rewrite] Sea water goes into shallow pits called salt pans and stays there.
- [model rewrite] The sun heats the water, turns it into vapor, and leaves salt as white crystals.

**Shown to the student: 3**  (2 written by the model, 1 fill-in-the-blank by code)

1. **From where is common salt obtained in the region of Gujarat and Tamil Nadu?**  _(model, from sentence 2)_
   - A) evaporation
   - B) mixture
   - C) shallow
   - D) sea  ✅
   - source: "Along the coasts of Gujarat and Tamil Nadu, a lot of our common salt is obtained from sea water."
2. **What is left behind as white crystals after evaporation?**  _(model, from sentence 4)_
   - A) grain
   - B) salt  ✅
   - C) separate
   - D) sea
   - source: "The heat of the sun slowly turns the water into vapour, a process called evaporation, and the salt is left behind as white crystals."
3. **Fill in the blank: The clear water above can then be poured off gently into another vessel without disturbing the _____, which is called decantation.**  _(code fill-in-the-blank, from sentence 9)_
   - A) grain
   - B) separate
   - C) husk
   - D) sand  ✅
   - source: "The clear water above can then be poured off gently into another vessel without disturbing the sand, which is called decantation."

**Held back: 3**

- RED, answer **sand**, sentence 9: "The clear water above can then be poured off gently into another vessel without disturbing the sand, which is called decantation."
  - draft "What is called decantation?"  [stem_answers_to_key]  → answered back: "water"
  - draft "What is called decantation?"  [stem_answers_to_key]  → answered back: "water"
  - draft "What is called decantation?"  [stem_answers_to_key]  → answered back: "water"
- RED, answer **particles**, sentence 10: "To remove the last fine particles, the water can be passed through filter paper."
  - draft "To remove the last fine particles, the water can be passed through filter paper."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "To remove the last fine particles, the water can be passed through filter paper."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "To remove the last fine particles, the water can be passed through filter paper."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
- RED, answer **mixture**, sentence 6: "Evaporation is one of several methods used to separate the parts of a mixture."
  - draft "What is one of the methods used to separate the parts of a mixture?"  [stem_no_answer_leak, stem_not_echo]
  - draft "What is one of the methods used to separate the parts of a mixture?"  [stem_no_answer_leak, stem_not_echo]
  - draft "What is one of the methods used to separate the parts of a mixture?"  [stem_no_answer_leak, stem_not_echo]

## chem_metals
*subject chemistry, class 8, style properties-list* · OK: 216 words · 18.1 s

**Summary**
- [model rewrite] Elements can be divided into metals and non-metals.
- [model rewrite] Metals and non-metals react differently with oxygen.
- [model rewrite] Metals form oxides that are basic, and non-metals form oxides that are acidic.

**Shown to the student: 3**  (2 written by the model, 1 fill-in-the-blank by code)

1. **What do metals and non-metals react with?**  _(model, from sentence 14)_
   - A) oxygen  ✅
   - B) nature
   - C) carbon
   - D) heat
   - source: "Metals and non-metals also react differently with oxygen."
2. **Which metal is used in cooking vessels?**  _(model, from sentence 5)_
   - A) iron
   - B) oxygen
   - C) differently
   - D) copper  ✅
   - source: "Metals are good conductors of heat and electricity, which is why cooking vessels are made of metal and electric wires are made of copper."
3. **Fill in the blank: They are poor conductors of heat and _____.**  _(code fill-in-the-blank, from sentence 9)_
   - A) iron
   - B) differently
   - C) broadly
   - D) electricity  ✅
   - source: "They are poor conductors of heat and electricity."

**Held back: 4**

- AMBER, answer **non-metals**, sentence 1: "Elements can be broadly divided into metals and non-metals."
  - draft "What is divided into? non-metals"  [stem_question_mark, stem_no_answer_leak]
  - draft "What is divided into? non-metals"  [stem_question_mark, stem_no_answer_leak]
  - draft "What are the categories of elements?"  [stem_in_passage]  → answered back: "metals and non-metals"
  - options: fittings | non-metals | bells | wires
- RED, answer **aluminium**, sentence 2: "Metals such as iron, copper, aluminium and gold are usually hard and shiny."
  - draft "What is used for making metal?"  [stem_answers_to_key]  → answered back: "metals"
  - draft "What is used to make food?"  [stem_answers_to_key]  → answered back: "food"
  - draft "What is one metal that is usually hard and shiny?"  [stem_answers_to_key]  → answered back: "aluminum"
- RED, answer **wires**, sentence 3: "They are malleable, which means they can be beaten into thin sheets, and ductile, which means they can be drawn into wires."
  - draft "Which of the following is a description of a material that can be beaten into thin sheets and drawn into wires?"  [stem_length, stem_no_answer_leak, stem_readability]
  - draft "Which of the following is a description of a material that can be beaten into thin sheets and drawn into wires?"  [stem_length, stem_no_answer_leak, stem_readability]
  - draft "Which of the following is a description of a material that can be beaten into thin sheets or drawn into wires?"  [stem_length, stem_no_answer_leak, stem_readability]
- RED, answer **differently**, sentence 7: "Non-metals such as sulphur, carbon, oxygen and phosphorus behave very differently."
  - draft "What do non-metals behave differently towards?"  [stem_no_answer_leak]
  - draft "What do non-metals behave differently with?"  [stem_no_answer_leak]
  - draft "What do non-metals such as sulphur, carbon, oxygen, and phosphorus behave differently like?"  [stem_no_answer_leak, stem_not_echo]

## chem_combustion
*subject chemistry, class 8, style cause-effect* · OK: 218 words · 18.8 s

**Summary**
- [model rewrite] The lowest temperature at which a substance catches fire is called the ignition temperature.
- [model rewrite] Kerosene catches fire easily, while wood needs more heat to ignite.
- [model rewrite] Water doesn't work with oil and petrol—because oil floats on water and keeps burning.

**Shown to the student: 3**  (1 written by the model, 2 fill-in-the-blank by code)

1. **What is needed to catch fire with kerosene?**  _(model, from sentence 5)_
   - A) fuel
   - B) supply
   - C) heated  ✅
   - D) extinguisher
   - source: "Kerosene has a low ignition temperature, so it catches fire easily, while wood must be heated much more."
2. **Fill in the blank: Covering a small fire with a _____ or sand works in the same way.**  _(code fill-in-the-blank, from sentence 13)_
   - A) heat
   - B) blanket  ✅
   - C) oxygen
   - D) water
   - source: "Covering a small fire with a blanket or sand works in the same way."
3. **Fill in the blank: For combustion to happen, three things are needed together: a fuel, air to supply oxygen, and enough heat to raise the fuel to its ignition _____.**  _(code fill-in-the-blank, from sentence 3)_
   - A) fire
   - B) temperature  ✅
   - C) burn
   - D) equipment
   - source: "For combustion to happen, three things are needed together: a fuel, air to supply oxygen, and enough heat to raise the fuel to its ignition temperature."

**Held back: 5**

- RED, answer **burning**, sentence 10: "Water is also not suitable for oil and petrol fires, because the oil floats on water and keeps burning."
  - draft "The oil floats on water and keeps burning, so water is not suitable for oil and petrol fires."  [stem_question_mark, stem_no_answer_leak]
  - draft "The oil floats on water and keeps burning."  [stem_question_mark, stem_no_answer_leak]
  - draft "The oil floats on water, so it keeps burning."  [stem_question_mark, stem_no_answer_leak]
- RED, answer **catches**, sentence 4: "The ignition temperature is the lowest temperature at which a substance catches fire."
  - draft "What is the lowest temperature at which a substance catches fire?"  [stem_no_answer_leak]
  - draft "What does a substance catch fire at?"  [stem_answers_to_key]  → answered back: "temperature"
  - draft "What do you call a substance that catches fire?"  [stem_no_answer_leak]
- RED, answer **equipment**, sentence 12: "Being heavier than air, it forms a blanket around the fire, cutting off the supply of oxygen, and it does not harm electrical equipment."
  - draft "What does the sentence describe?"  [stem_in_passage, stem_answers_to_key]  → answered back: "the Ganga river begins in the Himalayas"
  - draft "What is the effect of being heavier than air?"  [stem_answers_to_key]  → answered back: "it cuts off the supply of oxygen"
  - draft "What does the sentence refer to?"  [stem_in_passage, stem_answers_to_key]  → answered back: "the fire"
- RED, answer **extinguisher**, sentence 6: "Removing any one of these three things puts a fire out, and this is the idea behind every fire extinguisher."
  - draft "What is the idea behind every fire extinguisher?"  [stem_no_answer_leak]
  - draft "What is the idea behind every fire extinguisher?"  [stem_no_answer_leak]
  - draft "What is the idea behind every fire extinguisher?"  [stem_no_answer_leak]
- RED, answer **water**, sentence 9: "But water should never be used on fires involving electrical equipment, because water conducts electricity and can give a shock."
  - draft "What should water not be used on?"  [stem_no_answer_leak]
  - draft "What should water never be used on?"  [stem_no_answer_leak]
  - draft "What is the correct term for water that should never be used on fires involving electrical equipment?"  [stem_no_answer_leak]

## bio_digestion
*subject biology, class 7, style process* · OK: 224 words · 19.5 s

**Summary**
- [model rewrite] Digestion breaks food into simple substances the body can absorb.
- [model rewrite] The acid kills the bacteria that come with food, and the juices break down proteins.
- [model rewrite] From the stomach, food goes into the small intestine, which is about 7.5 metres long and is tightly coiled.

**Shown to the student: 3**  (2 written by the model, 1 fill-in-the-blank by code)

1. **What happens to the proteins in the juices?**  _(model, from sentence 8)_
   - A) break  ✅
   - B) inner
   - C) absorb
   - D) intestine
   - source: "The acid kills many bacteria that enter with the food, and the juices begin to break down proteins."
2. **What is the body of the food pipe moving in?**  _(model, from sentence 5)_
   - A) intestine
   - B) digestion
   - C) saliva
   - D) stomach  ✅
   - source: "The walls of the food pipe contract and relax in waves, moving the food down to the stomach."
3. **Fill in the blank: Here the food is completely digested with the help of bile from the liver and _____ from the pancreas.**  _(code fill-in-the-blank, from sentence 10)_
   - A) saliva
   - B) absorb
   - C) juice  ✅
   - D) blood
   - source: "Here the food is completely digested with the help of bile from the liver and juice from the pancreas."

**Held back: 4**

- RED, answer **absorb**, sentence 1: "Digestion is the process of breaking down food into simple substances that the body can absorb."
  - draft "What is the process of breaking down food into simple substances that the body can absorb?"  [stem_no_answer_leak, stem_not_echo]
  - draft "What is the process of breaking down food into simple substances that the body can absorb?"  [stem_no_answer_leak, stem_not_echo]
  - draft "What is the process of breaking down food into simple substances called?"  [stem_answers_to_key]  → answered back: "digestion"
- RED, answer **7.5**, sentence 9: "From the stomach, the partly digested food passes into the small intestine, which is about 7.5 metres long and is tightly coiled."
  - draft "The length of the small intestine is about 7.5 metres."  [stem_question_mark, stem_no_answer_leak]
  - draft "The length of the small intestine is about 7.5 meters."  [stem_question_mark, stem_no_answer_leak]
  - draft "The small intestine is about 7.5 metres long and is tightly coiled."  [stem_question_mark, stem_no_answer_leak]
- RED, answer **blood**, sentence 12: "They greatly increase the surface area for absorption, and the digested food passes through them into the blood vessels."
  - draft "The blood carries the digested food to where?"  [stem_no_answer_leak]
  - draft "The blood carries the digested food to where?"  [stem_no_answer_leak]
  - draft "The blood transports digested food to the body."  [stem_question_mark, stem_no_answer_leak]
- RED, answer **pipe**, sentence 4: "The tongue mixes the food with saliva and pushes it down into the food pipe, or oesophagus."
  - draft "What is the food pipe?"  [stem_no_answer_leak]
  - draft "What is the name of the food pipe?"  [stem_no_answer_leak]
  - draft "What is the name of the part where food is pushed down into the oesophagus?"  [stem_answers_to_key]  → answered back: "oesophagus"

## bio_respiration
*subject biology, class 7, style misconception* · OK: 218 words · 20.4 s

**Summary**
- [model rewrite] In respiration, glucose from food is broken down into energy, which the cells use for all activities.
- [model rewrite] When oxygen is used, glucose is broken down into carbon dioxide and water. This is called aerobic respiration.

**Shown to the student: 3**  (1 written by the model, 2 fill-in-the-blank by code)

1. **What is a common mistake in thinking about plants?**  _(model, from sentence 13)_
   - A) muscle
   - B) respire  ✅
   - C) oxygen
   - D) glucose
   - source: "It is a common mistake to think that plants respire only at night."
2. **Fill in the blank: When there is not enough oxygen, glucose is _____ down only partly.**  _(code fill-in-the-blank, from sentence 8)_
   - A) broken  ✅
   - B) respiration
   - C) breathe
   - D) respire
   - source: "When there is not enough oxygen, glucose is broken down only partly."
3. **Fill in the blank: During hard exercise, our leg muscles may respire anaerobically and _____ lactic acid, which causes cramps.**  _(code fill-in-the-blank, from sentence 10)_
   - A) produce  ✅
   - B) breathe
   - C) chest
   - D) respiration
   - source: "During hard exercise, our leg muscles may respire anaerobically and produce lactic acid, which causes cramps."

**Held back: 5**

- RED, answer **muscle**, sentence 6: "In respiration, glucose from our food is broken down to release energy, which the cells use for every activity, from moving a muscle to thinking."
  - draft "In respiration, glucose is broken down to release energy, which the cells use for every activity, from moving a muscle to thinking."  [stem_question_mark, stem_length, stem_no_answer_leak, stem_not_echo]
  - draft "In respiration, glucose is broken down to release energy, which the cells use for every activity, from moving a muscle to thinking."  [stem_question_mark, stem_length, stem_no_answer_leak, stem_not_echo]
  - draft "In respiration, glucose from our food is broken down to release energy, which the cells use for every activity, from moving a muscle to thinking."  [stem_question_mark, stem_length, stem_no_answer_leak, stem_not_echo]
- RED, answer **dioxide**, sentence 7: "When oxygen is used, the glucose is broken down completely into carbon dioxide and water, and this is called aerobic respiration."
  - draft "What is the result of the process called aerobic respiration?"  [stem_answers_to_key]  → answered back: "it produces energy in the form of ATP"
  - draft "What is the result of the process called aerobic respiration?"  [stem_answers_to_key]  → answered back: "it produces energy in the form of ATP"
  - draft "What is called when oxygen is used for respiration?"  [stem_answers_to_key]  → answered back: "aerobic respiration"
- RED, answer **breathing**, sentence 1: "Many people use the words breathing and respiration as if they mean the same thing, but they are different processes."
  - draft "What do people use to breathe?"  [stem_answers_to_key]  → answered back: "breathe"
  - draft "What do people use to breathe?"  [stem_answers_to_key]  → answered back: "breathe"
  - draft "What do people use to breathe?"  [stem_answers_to_key]  → answered back: "breathe"
- RED, answer **cells**, sentence 5: "Respiration is what happens inside the cells of the body."
  - draft "What happens inside the cells of the body?"  [stem_no_answer_leak]
  - draft "What happens inside the cells of the body?"  [stem_no_answer_leak]
  - draft "What happens inside the cells of the body?"  [stem_no_answer_leak]
- RED, answer **lungs**, sentence 3: "When we breathe in, the chest cavity expands and air rushes into the lungs."
  - draft "When we breathe in, the air rushes into the lungs."  [stem_question_mark, stem_no_answer_leak]
  - draft "When we breathe in, the air rushes into the lungs."  [stem_question_mark, stem_no_answer_leak]
  - draft "When we breathe, the air rushes into the lungs."  [stem_question_mark, stem_no_answer_leak]

## bio_pitcher
*subject biology, class 7, style puzzle-explanation* · OK: 214 words · 15.2 s

**Summary**
- [model rewrite] Most green plants make their own food, but a few also trap insects.
- [model rewrite] The pitcher plant is one of them.
- [model rewrite] Why should a green plant that makes its own food catch insects at all?

**Shown to the student: 3**  (2 written by the model, 1 fill-in-the-blank by code)

1. **What do some plants trap?**  _(model, from sentence 1)_
   - A) insects  ✅
   - B) downwards
   - C) attracts
   - D) hills
   - source: "Most green plants make their own food, but a few plants also trap insects."
2. **What nutrient do pitcher plants need to make proteins?**  _(model, from sentence 11)_
   - A) rim
   - B) jug
   - C) nitrogen  ✅
   - D) tip
   - source: "Pitcher plants usually grow in soil that is poor in nitrogen, a nutrient that all plants need to make proteins."
3. **Fill in the blank: The answer lies in the _____.**  _(code fill-in-the-blank, from sentence 10)_
   - A) nitrogen
   - B) trap
   - C) leaf
   - D) soil  ✅
   - source: "The answer lies in the soil."

**Held back: 4**

- RED, answer **pitcher**, sentence 2: "The pitcher plant is one of them."
  - draft "The pitcher plant is one of them."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "The pitcher plant is one of them."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "The answer is: pitcher."  [stem_question_mark, stem_no_answer_leak]
- RED, answer **Venus**, sentence 14: "Other insect-eating plants include the Venus flytrap and the sundew."
  - draft "Which insect-eating plant is known as the Venus flytrap?"  [stem_no_answer_leak]
  - draft "Which insect-eating plant is known as the Venus flytrap?"  [stem_no_answer_leak]
  - draft "Which insect-eating plants include the Venus flytrap?"  [stem_no_answer_leak]
- RED, answer **India**, sentence 3: "It is found in the hills of Meghalaya and in some other parts of north-eastern India."
  - draft "Where is the Ganga river found?"  [stem_in_passage, stem_answers_to_key]  → answered back: "hills of Meghalaya"
  - draft "Where is the Ganga river found?"  [stem_in_passage, stem_answers_to_key]  → answered back: "hills of Meghalaya"
  - draft "Where is the Ganga river found?"  [stem_in_passage, stem_answers_to_key]  → answered back: "hills of Meghalaya"
- RED, answer **inside**, sentence 6: "When an insect lands on the rim, it slips and falls inside."
  - draft "When an insect lands on the rim, it slips and falls inside."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "When an insect lands on the rim, it slips and falls inside."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "When an insect lands on the rim, it slips and falls inside."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]

## bio_heart
*subject biology, class 10, style structure-numbers* · OK: 241 words · 18.3 s

**Summary**
- [model rewrite] The right side of the heart gets blood that has given its oxygen to the body and sends it to the lungs.
- [model rewrite] This oxygen-rich blood goes back to the left side of the heart, which sends it to the rest of the body.

**Shown to the student: 3**  (2 written by the model, 1 fill-in-the-blank by code)

1. **Which organ sends oxygen to the body?**  _(model, from sentence 5)_
   - A) ventricles
   - B) lungs  ✅
   - C) beats
   - D) pumps
   - source: "The right side of the heart receives blood that has given its oxygen to the body and sends it to the lungs."
2. **What is taken up by the blood in the lungs?**  _(model, from sentence 6)_
   - A) fist
   - B) wall
   - C) oxygen  ✅
   - D) heart
   - source: "In the lungs the blood picks up fresh oxygen and gets rid of carbon dioxide."
3. **Fill in the blank: It lies in the chest, slightly towards the left, and it _____ blood to all parts of the body without stopping, all through our lives.**  _(code fill-in-the-blank, from sentence 2)_
   - A) beats
   - B) pumps  ✅
   - C) valves
   - D) arteries
   - source: "It lies in the chest, slightly towards the left, and it pumps blood to all parts of the body without stopping, all through our lives."

**Held back: 4**

- RED, answer **rest**, sentence 7: "This oxygen-rich blood returns to the left side of the heart, which pumps it to the rest of the body."
  - draft "Which part of the body receives the oxygen-rich blood?"  [stem_answers_to_key]  → answered back: "left side of the heart"
  - draft "Which part of the body receives the oxygen-rich blood?"  [stem_answers_to_key]  → answered back: "left side of the heart"
  - draft "Which part of the heart pumps blood to the rest of the body?"  [stem_no_answer_leak]
- RED, answer **valves**, sentence 11: "Blood returns to the heart through veins, which have thinner walls and contain valves of their own."
  - draft "Which structures contain valves?"  [stem_no_answer_leak, stem_readability]
  - draft "Which part of the heart contains valves?"  [stem_no_answer_leak]
  - draft "Which part of the body has valves?"  [stem_no_answer_leak]
- RED, answer **pulse**, sentence 12: "Each contraction of the heart is a heartbeat, and the push of blood in the arteries can be felt as the pulse at the wrist."
  - draft "What is felt as the pulse at the wrist?"  [stem_no_answer_leak]
  - draft "What is felt as the pulse at the wrist?"  [stem_no_answer_leak]
  - draft "What is felt as the pulse at the wrist?"  [stem_no_answer_leak]
- RED, answer **walls**, sentence 10: "Blood leaves the heart through arteries, which have thick, elastic walls because the blood in them is under high pressure."
  - draft "The blood in the arteries is under high pressure because of the thick, elastic walls."  [stem_question_mark, stem_no_answer_leak]
  - draft "The walls of the arteries are elastic because the blood is under high pressure."  [stem_question_mark, stem_no_answer_leak]
  - draft "The walls of the arteries are elastic because the blood in them is under high pressure."  [stem_question_mark, stem_no_answer_leak]

## bio_microbes
*subject biology, class 8, style examples-history* · OK: 213 words · 20.5 s

**Summary**
- [model rewrite] In 1929, Alexander Fleming noticed that a mold was growing on one of his plates and stopped the growth of bacteria around it.
- [model rewrite] Antibiotics kill or stop disease-causing bacteria, but they don't work against viruses like the ones that cause the common cold.

**Shown to the student: 3**  (1 written by the model, 2 fill-in-the-blank by code)

1. **What does the same kind of bacteria help in doing?**  _(model, from sentence 6)_
   - A) microorganisms
   - B) making  ✅
   - C) milk
   - D) yeast
   - source: "The same kind of bacteria helps in making cheese and pickles."
2. **Fill in the blank: Although some cause diseases, many _____ are very useful to us.**  _(code fill-in-the-blank, from sentence 3)_
   - A) fungus
   - B) microorganisms  ✅
   - C) converts
   - D) multiplies
   - source: "Although some cause diseases, many microorganisms are very useful to us."
3. **Fill in the blank: In 1929 Alexander Fleming noticed that a mould growing on one of his plates had stopped the _____ of bacteria around it.**  _(code fill-in-the-blank, from sentence 10)_
   - A) antibiotic
   - B) growth  ✅
   - C) yeast
   - D) soil
   - source: "In 1929 Alexander Fleming noticed that a mould growing on one of his plates had stopped the growth of bacteria around it."

**Held back: 5**

- RED, answer **growth**, sentence 10: "In 1929 Alexander Fleming noticed that a mould growing on one of his plates had stopped the growth of bacteria around it."
  - draft "What happened to the bacteria around the growing mould?"  [stem_answers_to_key]  → answered back: "the bacteria stopped growing"
  - draft "What happened to the bacteria around the growing mould?"  [stem_answers_to_key]  → answered back: "the bacteria stopped growing"
  - draft "What happens when a bacteria grows on a plate?"  [stem_answers_to_key]  → answered back: "bacteria die on the plate"
- RED, answer **algae**, sentence 13: "In the soil, some bacteria and blue-green algae fix nitrogen from the air and make the soil more fertile."
  - draft "What do the algae fix from the air?"  [stem_no_answer_leak]
  - draft "What do the algae fix from the air?"  [stem_no_answer_leak]
  - draft "What makes the soil more fertile in the soil?"  [stem_answers_to_key]  → answered back: "nitrogen from the air"
- RED, answer **curd**, sentence 4: "When a little curd is added to warm milk and left for a few hours, the milk sets into curd."
  - draft "What is the result of adding curd to warm milk?"  [stem_no_answer_leak]
  - draft "What is the result of adding curd to warm milk?"  [stem_no_answer_leak]
  - draft "What is the curd made of?"  [stem_no_answer_leak]
- RED, answer **batter**, sentence 7: "Yeast, a fungus, is used in making bread, idli and dosa batter."
  - draft "What is used in making bread, idli, and dosa batter?"  [stem_no_answer_leak]
  - draft "What is used in making bread, idli, and dosa batter?"  [stem_no_answer_leak]
  - draft "What is used in making bread, idli and dosa batter?"  [stem_no_answer_leak]
- RED, answer **antibiotic**, sentence 11: "From this mould the first antibiotic, penicillin, was made."
  - draft "What is the name of the first antibiotic made from this mould?"  [stem_no_answer_leak]
  - draft "What is the name of the first antibiotic, penicillin?"  [stem_no_answer_leak]
  - draft "What is the first antibiotic made from?"  [stem_no_answer_leak]

## bio_pollination
*subject biology, class 7, style process* · OK: 223 words · 16.0 s

**Summary**
- [model rewrite] Flowers are the parts that make up a plant.
- [model rewrite] The male part of a flower is the stamen, which makes pollen come out.
- [model rewrite] If the pollen lands on the stigma of the same flower, it is called self-pollination.

**Shown to the student: 3**  (1 written by the model, 2 fill-in-the-blank by code)

1. **What is called the transfer of pollen from the stamen to the stigma?**  _(model, from sentence 5)_
   - A) pollination  ✅
   - B) wind
   - C) cell
   - D) plant
   - source: "The transfer of pollen from the stamen to the stigma is called pollination."
2. **Fill in the blank: After pollination, the pollen grain grows a tube down to the ovule, and the male cell joins the _____ cell.**  _(code fill-in-the-blank, from sentence 12)_
   - A) water
   - B) reproductive
   - C) wind
   - D) egg  ✅
   - source: "After pollination, the pollen grain grows a tube down to the ovule, and the male cell joins the egg cell."
3. **Fill in the blank: Wind carries the light, dry _____ of maize and grasses over long distances.**  _(code fill-in-the-blank, from sentence 9)_
   - A) ovary
   - B) pistil
   - C) pollen  ✅
   - D) male
   - source: "Wind carries the light, dry pollen of maize and grasses over long distances."

**Held back: 5**

- RED, answer **grains**, sentence 2: "The male part of a flower is the stamen, which produces pollen grains."
  - draft "What is produced by the stamen of a flower?"  [stem_answers_to_key]  → answered back: "pollen"
  - draft "What is produced by the stamen? grains"  [stem_question_mark, stem_no_answer_leak]
  - draft "What is produced by the male part of a flower?"  [stem_answers_to_key]  → answered back: "pollen"
- RED, answer **plant**, sentence 1: "Flowers are the reproductive parts of a plant."
  - draft "What is the reproductive part of a plant?"  [stem_no_answer_leak]
  - draft "What is the reproductive part of a plant?"  [stem_no_answer_leak]
  - draft "What is the reproductive part of a plant?"  [stem_no_answer_leak]
- RED, answer **stigma**, sentence 6: "If the pollen lands on the stigma of the same flower, it is called self-pollination."
  - draft "What is called when pollen lands on the stigma of the same flower?"  [stem_no_answer_leak]
  - draft "What is called when the pollen lands on the stigma of the same flower?"  [stem_no_answer_leak]
  - draft "What is called when the pollen lands on the stigma of the same flower?"  [stem_no_answer_leak]
- RED, answer **carried**, sentence 11: "As they move from flower to flower, pollen sticks to their bodies and is carried along."
  - draft "What is carried along from flower to flower?"  [stem_no_answer_leak]
  - draft "What is carried along from flower to flower?"  [stem_no_answer_leak]
  - draft "What is carried along?"  [stem_no_answer_leak]
- RED, answer **ovary**, sentence 3: "The female part is the pistil, which contains the ovules in its lower part, the ovary."
  - draft "What part contains the ovules in its lower part?"  [stem_answers_to_key]  → answered back: "pistil"
  - draft "What part contains the ovules in its lower part?"  [stem_answers_to_key]  → answered back: "pistil"
  - draft "What part of the plant contains the ovules and the ovary?"  [stem_no_answer_leak]

## bio_xylem
*subject biology, class 9, style counterintuitive* · OK: 225 words · 16.6 s

**Summary**
- [model rewrite] A plant needs to move water from its roots to leaves that are far up high. It does this without a pump.
- [model rewrite] As water moves up from the leaves, it creates a pull that draws more water up the xylem, like drinking through a straw.

**Shown to the student: 5**  (5 written by the model, 0 fill-in-the-blank by code)

1. **What is the term for the tissue that transports water from the roots to the leaves?**  _(model, from sentence 2)_
   - A) phloem
   - B) job
   - C) dead
   - D) xylem  ✅
   - source: "The water travels through a tissue called xylem."
2. **What is the main part that plants use to get water from the ground?**  _(model, from sentence 1)_
   - A) travels
   - B) continuous
   - C) roots  ✅
   - D) contents
   - source: "A plant must move water from its roots to leaves that may be many metres above the ground, and it does this without a pump."
3. **What is the name of the tube that water enters from the soil?**  _(model, from sentence 7)_
   - A) continuous
   - B) contents
   - C) pipes
   - D) tubes  ✅
   - source: "Water enters the roots from the soil and is pulled up through these tubes."
4. **What remains after plants mature?**  _(model, from sentence 5)_
   - A) pipes  ✅
   - B) cells
   - C) travels
   - D) tubes
   - source: "As they mature, they lose their living contents, and the cross walls between them break down, leaving hollow, continuous pipes."
5. **What are the main cells of phloem?**  _(model, from sentence 11)_
   - A) roots
   - B) tissue
   - C) drinking
   - D) living  ✅
   - source: "Unlike xylem, the main cells of phloem are living."

**Held back: 1**

- RED, answer **transpiration**, sentence 13: "A large tree may lose hundreds of litres of water on a hot day through transpiration."
  - draft "What is transpiration?"  [stem_no_answer_leak, stem_readability]
  - draft "What is transpiration?"  [stem_no_answer_leak, stem_readability]
  - draft "What is transpiration?"  [stem_no_answer_leak, stem_readability]

## bio_vaccine
*subject biology, class 8, style history-story* · OK: 225 words · 22.2 s

**Summary**
- [model rewrite] In the eighteenth century, smallpox was one of the most feared diseases in the world.
- [model rewrite] Milkmaids who caught cowpox didn't get smallpox.
- [model rewrite] Some weeks later, Jenner exposed him to smallpox, and the boy did not fall sick.

**Shown to the student: 3**  (0 written by the model, 3 fill-in-the-blank by code)

1. **Fill in the blank: Vaccines have since been made against many diseases, including _____, measles and tetanus.**  _(code fill-in-the-blank, from sentence 14)_
   - A) polio  ✅
   - B) disease
   - C) century
   - D) eighteenth
   - source: "Vaccines have since been made against many diseases, including polio, measles and tetanus."
2. **Fill in the blank: When it enters the body, the body produces antibodies to fight these _____, and it remembers how to make them.**  _(code fill-in-the-blank, from sentence 12)_
   - A) milkmaids
   - B) measles
   - C) contains
   - D) germs  ✅
   - source: "When it enters the body, the body produces antibodies to fight these germs, and it remembers how to make them."
3. **Fill in the blank: The _____ became slightly ill and then recovered.**  _(code fill-in-the-blank, from sentence 7)_
   - A) vaccination
   - B) vaccine
   - C) boy  ✅
   - D) disease
   - source: "The boy became slightly ill and then recovered."

**Held back: 6**

- RED, answer **Jenner**, sentence 8: "Some weeks later, Jenner exposed him to smallpox, and the boy did not fall sick."
  - draft "Jenner"  [stem_question_mark, stem_no_answer_leak, stem_readability]
  - draft "Jenner"  [stem_question_mark, stem_no_answer_leak, stem_readability]
  - draft "Jenner"  [stem_question_mark, stem_no_answer_leak, stem_readability]
- RED, answer **diseases**, sentence 1: "In the eighteenth century, smallpox was one of the most feared diseases in the world."
  - draft "What was one of the most feared diseases in the world in the eighteenth century?"  [stem_no_answer_leak]
  - draft "What were the feared diseases in the eighteenth century?"  [stem_no_answer_leak]
  - draft "What were the most feared diseases in the world in the eighteenth century?"  [stem_no_answer_leak]
- RED, answer **cows**, sentence 4: "Milkmaids who had caught cowpox, a mild disease from cows, did not seem to get smallpox."
  - draft "What disease from cows did the milkmaids not get?"  [stem_no_answer_leak]
  - draft "What disease from cows was not getting smallpox?"  [stem_no_answer_leak]
  - draft "What is the disease that milkmaids who caught cowpox were not exposed to?"  [stem_answers_to_key]  → answered back: "cowpox"
- AMBER, answer **1980**, sentence 15: "After a worldwide vaccination campaign, smallpox was declared eradicated in 1980."
  - draft "When was smallpox declared eradicated?"  [passed]  → answered back: "1980"
- RED, answer **Phipps**, sentence 6: "He took material from a cowpox sore on the hand of a milkmaid and put it into a small cut on the arm of a boy named James Phipps."
  - draft "James Phipps was named after whom?"  [stem_no_answer_leak]
  - draft "James Phipps was named after whom?"  [stem_no_answer_leak]
  - draft "James Phipps was a boy named ..."  [stem_question_mark, stem_no_answer_leak]
- AMBER, answer **disease**, sentence 13: "If the real germs attack later, the body can destroy them quickly, before they cause disease."
  - draft "What is the result of the attack?"  [stem_in_passage]  → answered back: "the result is disease"
  - draft "What is the result of the attack?"  [stem_in_passage]  → answered back: "the result is disease"
  - draft "What does the sentence suggest about disease?"  [stem_no_answer_leak, stem_in_passage]
  - options: disease | smallpox | cowpox | boy

## his_ashoka
*subject history, class 6, style names-dates* · OK: 217 words · 16.2 s

**Summary**
- [model rewrite] Ashoka became king around 268 BCE and ruled a big empire with his capital at Pataliputra, near where Patna is now.
- [model rewrite] After eight years, Ashoka fought a war to conquer Kalinga, which is now in Odisha.

**Shown to the student: 3**  (3 written by the model, 0 fill-in-the-blank by code)

1. **Where did Ashoka fight a war to conquer Kalinga?**  _(model, from sentence 4)_
   - A) Odisha  ✅
   - B) BCE
   - C) Maurya
   - D) India
   - source: "About eight years after he became king, Ashoka fought a war to conquer Kalinga, in present-day Odisha."
2. **What is Ashoka's dhamma?**  _(model, from sentence 9)_
   - A) became
   - B) dynasty
   - C) religion  ✅
   - D) war
   - source: "Ashoka's dhamma was not a new religion."
3. **What did Ashoka decide not to fight wars for?**  _(model, from sentence 7)_
   - A) ancient
   - B) present-day
   - C) dhamma
   - D) war  ✅
   - source: "Ashoka was so filled with sorrow at the suffering he saw that he decided never to fight a war of conquest again."

**Held back: 3**

- RED, answer **India**, sentence 1: "Ashoka was one of the most famous rulers of ancient India."
  - draft "Which of the following is a famous ruler of ancient India?"  [stem_no_answer_leak]
  - draft "Which of the following is an example of a famous ruler of ancient India?"  [stem_no_answer_leak, stem_readability]
  - draft "Which of the following is an example of a ruler?"  [stem_answers_to_key]  → answered back: "Ashoka"
- RED, answer **Patna**, sentence 3: "Ashoka became king in about 268 BCE and ruled a vast empire with its capital at Pataliputra, near present-day Patna."
  - draft "Where did Ashoka become king?"  [stem_answers_to_key]  → answered back: "Pataliputra"
  - draft "Where did Ashoka become king?"  [stem_answers_to_key]  → answered back: "Pataliputra"
  - draft "Where did Ashoka become king?"  [stem_answers_to_key]  → answered back: "Pataliputra"
- RED, answer **empire**, sentence 11: "To spread these ideas, Ashoka had his messages carved on rocks and on polished stone pillars across his empire."
  - draft "To spread these ideas, Ashoka had his messages carved on rocks and on polished stone pillars across his empire."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "To spread these ideas, Ashoka had his messages carved on rocks and on polished stone pillars across his empire."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "To spread these ideas, Ashoka had his messages carved on rocks and on polished stone pillars across his empire."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]

## his_1857
*subject history, class 8, style dense-dates-names* · OK: 218 words · 17.7 s

**Summary**
- [model rewrite] The revolt of 1857 was the biggest challenge for British rule in India in the nineteenth century.
- [model rewrite] It started with Indian soldiers from the East India Company's army.
- [model rewrite] In 1858, the British government took over India.

**Shown to the student: 3**  (3 written by the model, 0 fill-in-the-blank by code)

1. **Where did Nana Saheb lead the rebels and fight bravely?**  _(model, from sentence 9)_
   - A) Bahadur
   - B) Indian
   - C) East
   - D) Jhansi  ✅
   - source: "Nana Saheb led the rebels at Kanpur, Begum Hazrat Mahal at Lucknow, and Rani Lakshmibai fought bravely at Jhansi."
2. **Where did the sepoys march to?**  _(model, from sentence 6)_
   - A) Zafar
   - B) Shah
   - C) Company
   - D) Delhi  ✅
   - source: "On 10 May, the sepoys at Meerut rebelled, freed their imprisoned comrades and marched to Delhi."
3. **On which date did the young soldier named Mangal Pandey attack his officers at Barrackpore?**  _(model, from sentence 5)_
   - A) Kanpur
   - B) East
   - C) Zafar
   - D) March  ✅
   - source: "On 29 March 1857, a young soldier named Mangal Pandey attacked his officers at Barrackpore and was later hanged."

**Held back: 3**

- RED, answer **India**, sentence 13: "In 1858 the British Parliament ended the rule of the East India Company and the British Crown took direct control of India."
  - draft "Where did the British Parliament end the rule of the East India Company?"  [stem_no_answer_leak]
  - draft "Where did the British Parliament end the rule of the East India Company?"  [stem_no_answer_leak]
  - draft "Where did the British Parliament end the rule of the East India Company in 1858?"  [stem_no_answer_leak]
- RED, answer **Company**, sentence 2: "It began as a rising of Indian soldiers, called sepoys, in the army of the East India Company."
  - draft "Which group of people did the Ganga river begin as?"  [stem_in_passage, stem_answers_to_key]  → answered back: "Indian soldiers"
  - draft "Which group of people is involved in the army of the East India Company?"  [stem_no_answer_leak, stem_in_passage]
  - draft "Which company led the army of India in the East?"  [stem_no_answer_leak]
- RED, answer **Zafar**, sentence 7: "There they proclaimed the old Mughal emperor, Bahadur Shah Zafar, as their leader."
  - draft "Where did the Ganga river begin?"  [stem_in_passage, stem_answers_to_key]  → answered back: "Himalayas"
  - draft "Where did the Ganga river begin?"  [stem_in_passage, stem_answers_to_key]  → answered back: "Himalayas"
  - draft "Where did the Ganga river begin?"  [stem_in_passage, stem_answers_to_key]  → answered back: "Himalayas"

## his_harappa
*subject history, class 6, style description-places* · OK: 223 words · 17.8 s

**Summary**
- [model rewrite] About 4,700 years ago, some of the earliest cities in the world grew along the river Indus and its tributaries.
- [model rewrite] The cities had good drains, covered with stones, running along the streets.

**Shown to the student: 3**  (2 written by the model, 1 fill-in-the-blank by code)

1. **What is covered with stones in the cities?**  _(model, from sentence 7)_
   - A) reservoirs
   - B) rooms
   - C) storeys
   - D) streets  ✅
   - source: "The cities had carefully planned drains, covered with stones, running along the streets."
2. **Where did some of the earliest cities grow up?**  _(model, from sentence 1)_
   - A) Dholavira
   - B) Mohenjodaro
   - C) Indus  ✅
   - D) Khadir
   - source: "About 4,700 years ago, some of the earliest cities in the world grew up along the river Indus and its tributaries."
3. **Fill in the blank: The houses were _____ of baked bricks of a standard size, and they were one or two storeys high, with rooms _____ around a courtyard.**  _(code fill-in-the-blank, from sentence 6)_
   - A) present-day
   - B) grew
   - C) river
   - D) built  ✅
   - source: "The houses were built of baked bricks of a standard size, and they were one or two storeys high, with rooms built around a courtyard."

**Held back: 4**

- RED, answer **Dholavira**, sentence 3: "Other important cities included Mohenjodaro, Lothal and Dholavira."
  - draft "Which of the following cities is mentioned in the sentence? Dholavira"  [stem_question_mark, stem_no_answer_leak, stem_in_passage]
  - draft "Which of the following cities is mentioned in the sentence? Dholavira"  [stem_question_mark, stem_no_answer_leak, stem_in_passage]
  - draft "Which of the following is an important city in India?"  [stem_in_passage, stem_answers_to_key]  → answered back: "Mohenjodaro"
- RED, answer **Harappan**, sentence 2: "These are called the Harappan cities, after Harappa, the first site of this civilisation to be discovered, in present-day Pakistan."
  - draft "The answer is: Harappan."  [stem_question_mark, stem_no_answer_leak, stem_in_passage]
  - draft "The name of the first Harappan city discovered is called?"  [stem_no_answer_leak]
  - draft "The name of the first Harappan city discovered is called?"  [stem_no_answer_leak]
- AMBER, answer **Gujarat**, sentence 9: "Dholavira, on the island of Khadir in the Rann of Kutch in Gujarat, is remarkable for its water storage."
  - draft "Where is Dholavira located?"  [stem_in_passage, stem_readability]  → answered back: "Gujarat"
  - draft "Where is Dholavira located?"  [stem_in_passage, stem_readability]  → answered back: "Gujarat"
  - draft "Where does Dholavira stand in relation to the Rann of Kutch?"  [stem_answers_to_key]  → answered back: "in the Rann of Kutch"
  - options: Indus | Pakistan | Harappa | Gujarat
- AMBER, answer **drains**, sentence 8: "Each house's drain was connected to these street drains."
  - draft "What is the name of the street drains?"  [stem_no_answer_leak]
  - draft "What is connected to the street drains?"  [stem_no_answer_leak]
  - draft "What is the name of the drain?"  [stem_in_passage]  → answered back: "street drains"
  - options: storeys | reservoirs | rooms | drains

## his_dandi
*subject history, class 8, style narrative-numbers* · OK: 213 words · 18.6 s

**Summary**
- [model rewrite] Yes, salt is something that every person needs in their food, so Gandhi saw the salt tax as a clear example of how the British government treated people.
- [model rewrite] The Salt March showed that ordinary people, by refusing to obey an unjust law, could challenge a powerful empire.

**Shown to the student: 3**  (0 written by the model, 3 fill-in-the-blank by code)

1. **Fill in the blank: This simple act was the beginning of the Civil Disobedience _____.**  _(code fill-in-the-blank, from sentence 8)_
   - A) India's
   - B) British
   - C) Ahmedabad
   - D) Movement  ✅
   - source: "This simple act was the beginning of the Civil Disobedience Movement."
2. **Fill in the blank: Women took part in large numbers, picketing shops that sold liquor and _____ goods.**  _(code fill-in-the-blank, from sentence 10)_
   - A) struggle
   - B) became
   - C) centre
   - D) foreign  ✅
   - source: "Women took part in large numbers, picketing shops that sold liquor and foreign goods."
3. **Fill in the blank: Salt is something that every person, rich or poor, needs in their food, so Mahatma Gandhi saw the salt tax as a clear example of unjust _____ rule.**  _(code fill-in-the-blank, from sentence 3)_
   - A) Dandi
   - B) India's
   - C) British  ✅
   - D) March
   - source: "Salt is something that every person, rich or poor, needs in their food, so Mahatma Gandhi saw the salt tax as a clear example of unjust British rule."

**Held back: 6**

- RED, answer **British**, sentence 3: "Salt is something that every person, rich or poor, needs in their food, so Mahatma Gandhi saw the salt tax as a clear example of unjust British rule."
  - draft "The answer is: British."  [stem_question_mark, stem_no_answer_leak, stem_in_passage]
  - draft "The answer is: British."  [stem_question_mark, stem_no_answer_leak, stem_in_passage]
  - draft "The salt tax was a clear example of unjust British rule."  [stem_question_mark, stem_no_answer_leak]
- RED, answer **March**, sentence 12: "The Salt March showed that ordinary people, by refusing to obey an unjust law without using violence, could challenge a powerful empire."
  - draft "What did the Salt March show?"  [stem_no_answer_leak]
  - draft "What did the Salt March show?"  [stem_no_answer_leak]
  - draft "What term describes a movement of people against a powerful government?"  [stem_answers_to_key]  → answered back: "civil disobedience"
- RED, answer **Gandhi**, sentence 7: "There Gandhi picked up a handful of salt from the seashore, breaking the salt law."
  - draft "Gandhi broke the salt law."  [stem_question_mark, stem_no_answer_leak]
  - draft "Gandhi broke the salt law"  [stem_question_mark, stem_no_answer_leak]
  - draft "Gandhi broke the salt law"  [stem_question_mark, stem_no_answer_leak]
- RED, answer **taxes**, sentence 9: "Across the country, people made salt from sea water, refused to buy foreign cloth and refused to pay taxes."
  - draft "Where did the people make salt from sea water and refuse to pay taxes?"  [stem_no_answer_leak]
  - draft "Where did the people make salt from sea water?"  [stem_answers_to_key]  → answered back: "the sea water"
  - draft "Where did the people make salt from sea water?"  [stem_answers_to_key]  → answered back: "the sea water"
- RED, answer **India's**, sentence 1: "In 1930, salt became the centre of India's struggle for freedom."
  - draft "In 1930, what was the centre of India's struggle for freedom?"  [stem_no_answer_leak, stem_not_echo]
  - draft "In 1930, what was India's struggle for freedom?"  [stem_no_answer_leak]
  - draft "In 1930, India's struggle for freedom was led by salt."  [stem_question_mark, stem_no_answer_leak]
- AMBER, answer **Gujarat**, sentence 6: "On 6 April they reached Dandi, a small village on the coast of Gujarat."
  - draft "Where did they reach on 6 April?"  [passed]  → answered back: "Gujarat"
  - options: Ashram | Gujarat | Sabarmati | Gandhi

## his_chola
*subject history, class 7, style rulers-art-process* · OK: 217 words · 18.3 s

**Summary**
- [model rewrite] Under Rajaraja I, who became king in 985, their power grew. His son, Rajendra I, also became king. Rajaraja built a strong army and navy, and he extended Chola rule to Sri Lanka and the Maldives.
- [model rewrite] The Cholas are especially remembered for their temples.

**Shown to the student: 3**  (0 written by the model, 3 fill-in-the-blank by code)

1. **Fill in the blank: In this method, a figure is first made of wax and covered with _____.**  _(code fill-in-the-blank, from sentence 12)_
   - A) chola
   - B) dynasty
   - C) built
   - D) clay  ✅
   - source: "In this method, a figure is first made of wax and covered with clay."
2. **Fill in the blank: Its tower rises about _____ metres high.**  _(code fill-in-the-blank, from sentence 8)_
   - source: "Its tower rises about 66 metres high."
3. **Fill in the blank: The bronze figures of Nataraja, the dancing _____, are among the finest examples.**  _(code fill-in-the-blank, from sentence 14)_
   - A) Nadu
   - B) Shiva  ✅
   - C) Kaveri
   - D) Cholas
   - source: "The bronze figures of Nataraja, the dancing Shiva, are among the finest examples."

**Held back: 6**

- RED, answer **Rajaraja**, sentence 2: "Their power grew greatly under Rajaraja I, who became king in 985 CE, and his son Rajendra I. Rajaraja built a strong army and navy and extended Chola rule to Sri Lanka and the Maldives."
  - draft "Who was the king of Chola rule in 985 CE?"  [stem_answers_to_key]  → answered back: "Rajendra I"
  - draft "Who became king in 985 CE?"  [stem_answers_to_key]  → answered back: "Rajendra I"
  - draft "Who became king after Rajaraja I?"  [stem_no_answer_leak]
- RED, answer **temples**, sentence 6: "The Cholas are especially remembered for their temples."
  - draft "What is remembered for their temples?"  [stem_no_answer_leak]
  - draft "What is remembered for their temples?"  [stem_no_answer_leak]
  - draft "What is remembered for their temples?"  [stem_no_answer_leak]
- AMBER, answer **Nadu**, sentence 1: "The Cholas were a powerful dynasty that ruled from the Kaveri delta in present-day Tamil Nadu."
  - draft "Which region does the Ganga river begin?"  [stem_in_passage, stem_answers_to_key]  → answered back: "Himalayas"
  - draft "Which region does the Ganga river begin?"  [stem_in_passage, stem_answers_to_key]  → answered back: "Himalayas"
  - draft "Which of the following is the correct answer?"  [stem_in_passage]  → answered back: "Tamil Nadu"
  - options: Nadu | Rajendra | Sri | Rajaraja
- AMBER, answer **bronze**, sentence 11: "Chola artists were also famous for their bronze statues, made by a method called lost-wax casting."
  - draft "What is the name of the method used by the Chola artists to make bronze statues?"  [stem_no_answer_leak]
  - draft "What was the method used by the Chola artists to make their bronze statues?"  [stem_no_answer_leak]
  - draft "What type of art was done by the Chola artists?"  [stem_in_passage]  → answered back: "bronze"
  - options: powerful | wax | north | bronze
- RED, answer **Asia**, sentence 4: "His armies marched to the Ganga in the north, and his navy attacked kingdoms in Southeast Asia."
  - draft "Where did his armies march to and attack?"  [stem_answers_to_key]  → answered back: "the north"
  - draft "Where did his armies march to and attack?"  [stem_answers_to_key]  → answered back: "the north"
  - draft "Where did his armies march to and attack?"  [stem_answers_to_key]  → answered back: "the north"
- RED, answer **Gangaikondacholapuram**, sentence 5: "To celebrate his victory in the north, he built a new capital called Gangaikondacholapuram."
  - draft "Where did he build a new capital called Gangaikondacholapuram to celebrate his victory?"  [stem_no_answer_leak, stem_readability]
  - draft "Where did he build a new capital called Gangaikondacholapuram to celebrate his victory?"  [stem_no_answer_leak, stem_readability]
  - draft "Where was he able to build a new capital called Gangaikondacholapuram to celebrate his victory?"  [stem_no_answer_leak, stem_readability]

## his_mughal
*subject history, class 7, style system-terms* · OK: 213 words · 21.8 s

**Summary**
- [model rewrite] Under Akbar, the people didn't live in their jagirs, and the emperor's officers made sure the taxes were fair.
- [model rewrite] To fix land revenue, Akbar's revenue minister, Todar Mal, did a careful survey of crop yields, prices, and the area over ten years.

**Shown to the student: 3**  (1 written by the model, 2 fill-in-the-blank by code)

1. **What does the policy of Sulh-i Kul refer to?**  _(model, from sentence 13)_
   - A) religions  ✅
   - B) emperors
   - C) jagirs
   - D) taxes
   - source: "Akbar also followed a policy called sulh-i kul, meaning universal peace, which did not discriminate between people of different religions."
2. **Fill in the blank: A mansabdar was a person who held a mansab, meaning a rank or position in the _____ service.**  _(code fill-in-the-blank, from sentence 4)_
   - A) emperor's  ✅
   - B) yields
   - C) assignments
   - D) jagirs
   - source: "A mansabdar was a person who held a mansab, meaning a rank or position in the emperor's service."
3. **Fill in the blank: He introduced the mansabdari _____.**  _(code fill-in-the-blank, from sentence 3)_
   - A) position
   - B) given
   - C) revenue
   - D) system  ✅
   - source: "He introduced the mansabdari system."

**Held back: 5**

- RED, answer **collected**, sentence 9: "Under Akbar, mansabdars did not live in their jagirs, and the emperor's officers made sure that the taxes collected were fair."
  - draft "What did the emperor's officers ensure that the taxes collected were fair?"  [stem_no_answer_leak]
  - draft "What did the emperor's officers ensure to collect?"  [stem_answers_to_key]  → answered back: "fair"
  - draft "What did the emperor ensure?"  [stem_in_passage, stem_answers_to_key]  → answered back: "fair taxes"
- RED, answer **crop**, sentence 10: "To fix the land revenue, Akbar's revenue minister, Todar Mal, carried out a careful survey of crop yields, prices and the area cultivated over ten years."
  - draft "What did Akbar's revenue minister, Todar Mal, do to fix land revenue?"  [stem_answers_to_key]  → answered back: "carried out a survey"
  - draft "What was the main goal of Akbar's revenue minister, Todar Mal?"  [stem_answers_to_key]  → answered back: "to fix land revenue"
  - draft "What did Akbar's revenue minister, Todar Mal, carry out?"  [stem_answers_to_key]  → answered back: "a careful survey of crop yields, prices and the area cultivated over ten years"
- AMBER, answer **Nama**, sentence 14: "Abul Fazl, a close friend of Akbar, wrote a history of his reign called the Akbar Nama."
  - draft "What did Abul Fazl write about his reign?"  [passed]  → answered back: "the Akbar Nama"
  - options: Mal | Todar | Nama | Mughal
- AMBER, answer **1605**, sentence 2: "Akbar, who ruled from 1556 to 1605, organised the administration with great care."
  - draft "When did Akbar rule?"  [stem_in_passage]  → answered back: "1556 to 1605"
  - draft "When did Akbar rule?"  [stem_in_passage]  → answered back: "1556 to 1605"
  - draft "When did Akbar rule from 1556 to 1605?"  [stem_no_answer_leak]
- RED, answer **cash**, sentence 11: "The tax was then fixed for each crop in cash."
  - draft "What is the tax paid in cash for each crop?"  [stem_no_answer_leak]
  - draft "What is the tax paid in cash for each crop?"  [stem_no_answer_leak]
  - draft "What is the cash used for?"  [stem_no_answer_leak, stem_in_passage]

## geo_monsoon
*subject geography, class 9, style cause-effect* · OK: 216 words · 21.9 s

**Summary**
- [model rewrite] Winds blow from high pressure to low pressure, so the ocean's moist winds move from the ocean to the land.
- [model rewrite] By October, the land cools and the winds reverse, blowing from the sea to the land.

**Shown to the student: 3**  (2 written by the model, 1 fill-in-the-blank by code)

1. **Which month does the land cool and the winds reverse?**  _(model, from sentence 13)_
   - A) June
   - B) Ghats
   - C) Arabic
   - D) October  ✅
   - source: "By October, the land cools and the winds reverse, blowing from the land towards the sea."
2. **What is the result of the moist winds forcing to rise over the Western Ghats?**  _(model, from sentence 10)_
   - A) blow
   - B) monsoon
   - C) ocean
   - D) rain  ✅
   - source: "When the moist winds are forced to rise over the Western Ghats, they cool and drop heavy rain on the western slopes."
3. **Fill in the blank: These are the south-west _____ winds.**  _(code fill-in-the-blank, from sentence 7)_
   - A) monsoon  ✅
   - B) climate
   - C) rain
   - D) land
   - source: "These are the south-west monsoon winds."

**Held back: 4**

- RED, answer **land**, sentence 6: "Winds blow from high pressure to low pressure, so moist winds from the ocean begin to move towards the land."
  - draft "Which of the following is a moist wind?"  [stem_answers_to_key]  → answered back: "Himalayas"
  - draft "Which of the following is NOT a type of wind?"  [stem_in_passage, stem_answers_to_key]  → answered back: "high pressure"
  - draft "Which of the following is NOT an example of a wind belt?"  [stem_in_passage, stem_answers_to_key]  → answered back: "Himalayas"
- RED, answer **seasons**, sentence 2: "India's climate is called a monsoon climate because the direction of the winds reverses with the seasons."
  - draft "The Ganga river begins at the glacier known as?"  [stem_in_passage, stem_answers_to_key]  → answered back: "Himalayas"
  - draft "The direction of the winds reverses with the seasons."  [stem_question_mark, stem_no_answer_leak]
  - draft "The Ganga river begins at which glacier?"  [stem_in_passage, stem_answers_to_key]  → answered back: "Gangotri"
- RED, answer **India**, sentence 4: "By May, an area of low pressure forms over the plains of north-western India."
  - draft "Where does the Ganga river begin?"  [stem_in_passage, stem_answers_to_key]  → answered back: "Himalayas"
  - draft "Where does the Ganga river begin?"  [stem_in_passage, stem_answers_to_key]  → answered back: "Himalayas"
  - draft "Where does the Ganga river begin?"  [stem_in_passage, stem_answers_to_key]  → answered back: "Himalayas"
- RED, answer **Ocean**, sentence 5: "The air over the Indian Ocean is cooler, so the pressure there is higher."
  - draft "What is the pressure in the Indian Ocean?"  [stem_no_answer_leak]
  - draft "What is the pressure in the Indian Ocean?"  [stem_no_answer_leak]
  - draft "What is the pressure in the Indian Ocean?"  [stem_no_answer_leak]

## geo_soils
*subject geography, class 10, style classification* · OK: 219 words · 17.3 s

**Summary**
- [model rewrite] Soil is important because most of our food grows in it.
- [model rewrite] Soil is made when rocks get broken down by things like temperature changes, running water, wind, and living things over a long time.

**Shown to the student: 3**  (1 written by the model, 2 fill-in-the-blank by code)

1. **What is the main factor that forms laterite soil?**  _(model, from sentence 12)_
   - A) broken
   - B) alluvial
   - C) widespread
   - D) temperature  ✅
   - source: "Laterite soil forms in areas with high temperature and heavy rainfall, where the rain washes away many nutrients."
2. **Fill in the blank: They get their _____ colour from iron.**  _(code fill-in-the-blank, from sentence 11)_
   - A) red  ✅
   - B) rocks
   - C) black
   - D) wind
   - source: "They get their red colour from iron."
3. **Fill in the blank: It is formed from volcanic _____ and is excellent for growing cotton.**  _(code fill-in-the-blank, from sentence 8)_
   - A) trees
   - B) nutrients
   - C) rocks  ✅
   - D) washes
   - source: "It is formed from volcanic rocks and is excellent for growing cotton."

**Held back: 5**

- RED, answer **Deccan**, sentence 10: "Red and yellow soils develop on old crystalline rocks in the eastern and southern parts of the Deccan."
  - draft "Where do the soils develop on old crystalline rocks in the Deccan?"  [stem_no_answer_leak]
  - draft "Where do the soils develop on old crystalline rocks in the Deccan?"  [stem_no_answer_leak]
  - draft "Where do the soils develop on old crystalline rocks in the eastern and southern parts of the Deccan?"  [stem_no_answer_leak, stem_not_echo]
- RED, answer **wind**, sentence 2: "Soil is formed when rocks are slowly broken down by changes in temperature, running water, wind and living things, over thousands of years."
  - draft "What is formed when rocks are slowly broken down by changes in temperature, running water, wind and living things over thousands of years?"  [stem_length, stem_no_answer_leak, stem_not_echo]
  - draft "What is formed when rocks are slowly broken down by changes in temperature, running water, wind and living things over thousands of years?"  [stem_length, stem_no_answer_leak, stem_not_echo]
  - draft "What is formed when rocks are slowly broken down by changes in temperature, running water, wind and living things, over thousands of years?"  [stem_length, stem_no_answer_leak, stem_not_echo]
- RED, answer **water**, sentence 15: "Soil erosion, the removal of the top layer of soil by wind and water, is a serious problem."
  - draft "What is a serious problem caused by soil erosion?"  [stem_answers_to_key]  → answered back: "soil erosion"
  - draft "What is a serious problem caused by soil erosion?"  [stem_answers_to_key]  → answered back: "soil erosion"
  - draft "What is a serious problem caused by soil erosion?"  [stem_answers_to_key]  → answered back: "soil erosion"
- AMBER, answer **Rajasthan**, sentence 14: "Arid soils, found in Rajasthan, are sandy and salty."
  - draft "Where are the arid soils found?"  [passed]  → answered back: "Rajasthan"
  - options: Brahmaputra | Indus | Rajasthan | Madhya
- AMBER, answer **Indus**, sentence 5: "It is deposited by rivers such as the Ganga, the Brahmaputra and the Indus, and it covers the northern plains."
  - draft "Which river deposits the most water?"  [passed]  → answered back: "the Indus"
  - options: Deccan | Maharashtra | Madhya | Indus

## geo_ghats
*subject geography, class 9, style description-names* · OK: 205 words · 23.1 s

**Summary**
- [model rewrite] The Western Ghats are a chain of mountains that runs parallel to the western coast of India, from Gujarat to Kerala and Tamil Nadu, for about 1,600 kilometers.
- [model rewrite] The Western Ghats are also where many important rivers come from, like Godavari, Krishna, and Kaveri, which help water to many people in southern India.

**Shown to the student: 3**  (1 written by the model, 2 fill-in-the-blank by code)

1. **What is the status of the region that includes many frogs and flowering plants?**  _(model, from sentence 7)_
   - A) richest
   - B) endemic  ✅
   - C) biodiversity
   - D) parallel
   - source: "Many frogs and flowering plants of the region are also endemic."
2. **Fill in the blank: The Neelakurinji, a shrub that covers the hills of Munnar in blue _____, blooms only once in twelve years.**  _(code fill-in-the-blank, from sentence 8)_
   - A) animals
   - B) flowers  ✅
   - C) mountains
   - D) hotspots
   - source: "The Neelakurinji, a shrub that covers the hills of Munnar in blue flowers, blooms only once in twelve years."
3. **Fill in the blank: The lion-tailed macaque, a monkey with a silver mane, and the _____ tahr, a wild goat that lives on grassy hilltops, are two examples.**  _(code fill-in-the-blank, from sentence 6)_
   - A) Nilgiri  ✅
   - B) Gujarat
   - C) Western
   - D) Tamil
   - source: "The lion-tailed macaque, a monkey with a silver mane, and the Nilgiri tahr, a wild goat that lives on grassy hilltops, are two examples."

**Held back: 5**

- RED, answer **India**, sentence 9: "The Western Ghats are also the source of many important rivers, such as the Godavari, the Krishna and the Kaveri, which supply water to millions of people in southern India."
  - draft "Which rivers supply water to millions of people in southern India?"  [stem_no_answer_leak]
  - draft "Which of the following rivers is the source of water in southern India?"  [stem_no_answer_leak]
  - draft "Which of the following rivers is the source of water in southern India?"  [stem_no_answer_leak]
- RED, answer **Ghats**, sentence 4: "The Western Ghats receive heavy rain from the south-west monsoon, and this supports thick evergreen forests on their western slopes."
  - draft "The answer is: Ghats."  [stem_question_mark, stem_no_answer_leak, stem_in_passage]
  - draft "The answer is: Ghats."  [stem_question_mark, stem_no_answer_leak, stem_in_passage]
  - draft "The answer is: Ghats."  [stem_question_mark, stem_no_answer_leak, stem_in_passage]
- RED, answer **World**, sentence 11: "Because of their importance, UNESCO declared the Western Ghats a World Heritage Site in 2012."
  - draft "The answer is: World."  [stem_question_mark, stem_no_answer_leak, stem_in_passage]
  - draft "The answer is: World."  [stem_question_mark, stem_no_answer_leak, stem_in_passage]
  - draft "The answer is: World."  [stem_question_mark, stem_no_answer_leak, stem_in_passage]
- RED, answer **Earth**, sentence 5: "Many of the species living there are endemic, which means they are found nowhere else on Earth."
  - draft "Where are the endemic species found?"  [stem_answers_to_key]  → answered back: "Himalayas"
  - draft "Where are the endemic species found?"  [stem_answers_to_key]  → answered back: "Himalayas"
  - draft "Where are the endemic species found?"  [stem_answers_to_key]  → answered back: "Himalayas"
- RED, answer **plants**, sentence 2: "They are older than the Himalayas and are one of the richest regions of the world for plants and animals."
  - draft "What is one of the richest regions of the world for plants and animals?"  [stem_no_answer_leak]
  - draft "What is the name of the region that is one of the richest regions of the world for plants and animals?"  [stem_length, stem_no_answer_leak]
  - draft "What is one of the richest regions of the world for plants and animals?"  [stem_no_answer_leak]

## geo_groundwater
*subject geography, class 7, style misconception* · OK: 220 words · 18.8 s

**Summary**
- [model rewrite] When we dig a well, we usually find water at some depth below the ground.
- [model rewrite] This water is called groundwater.
- [model rewrite] When it rains, some of the water gets soaked into the ground.

**Shown to the student: 3**  (1 written by the model, 2 fill-in-the-blank by code)

1. **What is called the upper level of this water-filled layer?**  _(model, from sentence 9)_
   - A) table  ✅
   - B) infiltration
   - C) surface
   - D) groundwater
   - source: "The upper level of this water-filled layer is called the water table."
2. **Fill in the blank: It rises after good _____ and falls when more water is drawn out than is put back.**  _(code fill-in-the-blank, from sentence 12)_
   - A) cracks
   - B) grains
   - C) lies
   - D) rains  ✅
   - source: "It rises after good rains and falls when more water is drawn out than is put back."
3. **Fill in the blank: Paving every surface with concrete also reduces _____.**  _(code fill-in-the-blank, from sentence 14)_
   - A) layer
   - B) infiltration  ✅
   - C) soil
   - D) table
   - source: "Paving every surface with concrete also reduces infiltration."

**Held back: 5**

- RED, answer **ground**, sentence 1: "When we dig a well, we usually find water at some depth below the ground."
  - draft "When we dig a well, we find water at some depth below the ground."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "When we dig a well, we usually find water at some depth below the ground."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "When we dig a well, we usually find water at what depth below the ground?"  [stem_no_answer_leak, stem_not_echo]
- AMBER, answer **groundwater**, sentence 2: "This water is called groundwater."
  - draft "What is called groundwater?"  [stem_no_answer_leak]
  - draft "What is the name of the water referred to in the sentence?"  [stem_in_passage]  → answered back: "groundwater"
  - draft "What is the name of the water?"  [stem_in_passage]  → answered back: "groundwater"
  - options: dig | soil | surface | groundwater
- RED, answer **flow**, sentence 10: "A layer of rock or soil that stores water and allows it to flow through is called an aquifer."
  - draft "What is called a layer of rock or soil that stores water and allows it to flow through?"  [stem_no_answer_leak]
  - draft "What is called an aquifer?"  [stem_answers_to_key]  → answered back: "water reservoirs"
  - draft "What is called a layer of rock or soil that stores water and allows it to flow through?"  [stem_no_answer_leak]
- RED, answer **rocks**, sentence 4: "Groundwater fills the tiny spaces between grains of sand and soil, and the cracks in rocks, much like water fills a sponge."
  - draft "What fills the spaces between grains of sand and soil, and the cracks in rocks?"  [stem_no_answer_leak]
  - draft "What fills the spaces between grains of sand and soil, and the cracks in rocks?"  [stem_no_answer_leak]
  - draft "What is filled by groundwater?"  [stem_answers_to_key]  → answered back: "sponge"
- RED, answer **spaces**, sentence 8: "Above this layer, the spaces between the particles become completely filled with water."
  - draft "What is filled with water between the particles?"  [stem_answers_to_key]  → answered back: "water"
  - draft "What is the term for the spaces between the particles in a liquid?"  [stem_no_answer_leak, stem_in_passage]
  - draft "What is filled with water between the particles?"  [stem_answers_to_key]  → answered back: "water"

## geo_seasons
*subject geography, class 6, style misconception-numbers* · OK: 227 words · 22.6 s

**Summary**
- [model rewrite] At any moment, the half of the Earth facing the Sun gets day, while the other half gets night.
- [model rewrite] When the sun is shining on you, the sun's rays are more direct and the days are longer, so it is summer.

**Shown to the student: 3**  (0 written by the model, 3 fill-in-the-blank by code)

1. **Fill in the blank: It is tilted at an angle of about _____ degrees, and it always points in the same direction in space.**  _(code fill-in-the-blank, from sentence 10)_
   - A) 6
   - B) 23.5  ✅
   - C) 24
   - D) 29
   - source: "It is tilted at an angle of about 23.5 degrees, and it always points in the same direction in space."
2. **Fill in the blank: This _____ is called revolution.**  _(code fill-in-the-blank, from sentence 7)_
   - A) orbit
   - B) summer
   - C) leap
   - D) movement  ✅
   - source: "This movement is called revolution."
3. **Fill in the blank: At any moment, the half of the _____ facing the Sun has day, while the other half has night.**  _(code fill-in-the-blank, from sentence 4)_
   - A) January
   - B) India
   - C) Earth  ✅
   - D) North
   - source: "At any moment, the half of the Earth facing the Sun has day, while the other half has night."

**Held back: 6**

- RED, answer **Earth**, sentence 4: "At any moment, the half of the Earth facing the Sun has day, while the other half has night."
  - draft "At any moment, the Earth faces the Sun and has day, while the other half has night."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "At any moment, the Earth faces the Sun, and the other half faces the Moon."  [stem_question_mark, stem_no_answer_leak, stem_in_passage]
  - draft "At any moment, half of the Earth faces the Sun and the other half faces the Moon."  [stem_question_mark, stem_no_answer_leak]
- RED, answer **summer**, sentence 12: "When it leans towards the Sun, the Sun's rays fall on it more directly and the days are longer, so it is summer there."
  - draft "When the sun is more directly towards the land, what happens? summer"  [stem_question_mark, stem_no_answer_leak]
  - draft "When the sun is more directly reflected on the land, it becomes summer."  [stem_question_mark, stem_no_answer_leak, stem_in_passage]
  - draft "When the sun leans towards you, what do you see? summer"  [stem_question_mark, stem_no_answer_leak]
- RED, answer **leans**, sentence 11: "Because of this tilt, the Northern Hemisphere leans towards the Sun for part of the year and away from it for another part."
  - draft "The tilt causes the Northern Hemisphere to lean towards the Sun for part of the year and away from it for another part."  [stem_question_mark, stem_length, stem_not_echo]
  - draft "The Northern Hemisphere leans towards the Sun for part of the year and away from it for another part."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "The tilt causes the Northern Hemisphere to lean towards the Sun for part of the year and away from it for another part."  [stem_question_mark, stem_length, stem_not_echo]
- AMBER, answer **24**, sentence 2: "It spins on its axis, an imaginary line through the North and South Poles, and one full spin takes about 24 hours."
  - draft "How long does it take for the Ganga river to spin once?"  [stem_in_passage]  → answered back: "24 hours"
  - draft "How long does it take for the Ganga river to spin around the North and South Poles?"  [passed]  → answered back: "24 hours"
  - options: 23.5 | 24 | 29 | 365
- RED, answer **29**, sentence 8: "Every four years the extra hours add up to one whole day, so February then has 29 days, and that year is called a leap year."
  - draft "What is the name of the year that has 29 days?"  [stem_no_answer_leak]
  - draft "What is the name of the year that has 29 days?"  [stem_no_answer_leak]
  - draft "What is the name of the year called a leap year?"  [stem_answers_to_key]  → answered back: "leap year"
- RED, answer **6**, sentence 6: "One full trip takes about 365 days and 6 hours, which is one year."
  - draft "What is the total time of a year?"  [stem_in_passage, stem_answers_to_key]  → answered back: "one year"
  - draft "What is the time duration of one full trip?"  [stem_in_passage, stem_answers_to_key]  → answered back: "one year"
  - draft "What is the time period of a trip that takes about 365 days and 6 hours?"  [stem_no_answer_leak]

## geo_sundarbans_ocr
*subject geography, class 7, style scanned-line-breaks* · OK: 223 words · 21.4 s

**Summary**
- [model rewrite] Mangroves are trees and shrubs that grow in salty water along the coast.
- [model rewrite] Mangroves have special roots that help solve this problem.
- [model rewrite] The Sundarbans get their name from the Sundari tree, one of the most common mangroves there.

**Shown to the student: 3**  (1 written by the model, 2 fill-in-the-blank by code)

1. **What do mangroves have that solve this problem?**  _(model, from sentence 6)_
   - A) roots  ✅
   - B) tides
   - C) shrubs
   - D) trees
   - source: "Mangroves have special roots that solve this problem."
2. **Fill in the blank: Twice a day, the tides flood the forest floor with sea _____, and then the _____ goes back.**  _(code fill-in-the-blank, from sentence 4)_
   - A) delta
   - B) largest
   - C) water  ✅
   - D) lie
   - source: "Twice a day, the tides flood the forest floor with sea water, and then the water goes back."
3. **Fill in the blank: The region is shared by India and Bangladesh, and it is the largest man- grove _____ in the world.**  _(code fill-in-the-blank, from sentence 2)_
   - A) forest  ✅
   - B) putra
   - C) coast
   - D) salty
   - source: "The region is shared by India and Bangladesh, and it is the largest man- grove forest in the world."

**Held back: 5**

- RED, answer **Sundarbans**, sentence 9: "The Sundarbans get their name from the sundari tree, one of the most common mangroves there."
  - draft "What is the name of the place where the Sundarbans get their name?"  [stem_no_answer_leak]
  - draft "What is the name of the region where the Sundarbans get their name?"  [stem_no_answer_leak]
  - draft "What is the name of the place where the Sundarbans get their name?"  [stem_no_answer_leak]
- RED, answer **Bengal**, sentence 1: "The Sundarbans lie in the delta formed by the Ganga, the Brahma- putra and the Meghna rivers, where they meet the Bay of Bengal."
  - draft "Where do the Ganga, Brahma-putra, and Meghna rivers meet?"  [stem_answers_to_key]  → answered back: "Himalayas"
  - draft "Where do the Ganga, Brahma-putra, and Meghna rivers meet?"  [stem_answers_to_key]  → answered back: "Himalayas"
  - draft "Where does the Ganga river meet the Bay of Bengal?"  [stem_no_answer_leak]
- RED, answer **coast**, sentence 3: "Mangroves are trees and shrubs that can grow in salty water along the coast."
  - draft "What do mangroves grow in?"  [stem_answers_to_key]  → answered back: "salty water"
  - draft "What do mangroves grow in?"  [stem_answers_to_key]  → answered back: "salty water"
  - draft "What do mangroves grow in?"  [stem_answers_to_key]  → answered back: "salty water"
- RED, answer **World**, sentence 14: "In 1987 the Indian part of the Sundarbans was declared a World Heritage Site by UNESCO."
  - draft "In 1987, the Indian part of the Sundarbans was declared a World Heritage Site by UNESCO."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "In 1987, the Indian part of the Sundarbans was declared a World Heritage Site by UNESCO."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "In 1987, the Indian part of the Sundarbans was declared a World Heritage Site by UNESCO."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
- RED, answer **plant**, sentence 8: "These breathing roots, called pneumatophores, take in air for the plant."
  - draft "What is the name of the breathing roots called?"  [stem_answers_to_key]  → answered back: "pneumatophores"
  - draft "What is the name of the plant that uses breathing roots called pneumatophores?"  [stem_no_answer_leak]
  - draft "What is the name of the breathing roots called?"  [stem_answers_to_key]  → answered back: "pneumatophores"

## civ_panchayat
*subject civics, class 6, style institution-process* · OK: 221 words · 18.9 s

**Summary**
- [kept original (rewrite failed checks)] In most villages of India, local matters are managed by an elected body called the Gram Panchayat.
- [model rewrite] The Gram Sabha chooses the people who are called ward members or panches, and the leader of the panchayat is called the sarpanch or pradhan.

**Shown to the student: 3**  (1 written by the model, 2 fill-in-the-blank by code)

1. **What is the elected body called in most villages of India?**  _(model, from sentence 1)_
   - A) Parishad
   - B) Zila
   - C) Samiti
   - D) Panchayat  ✅
   - source: "In most villages of India, local matters are managed by an elected body called the Gram Panchayat."
2. **Fill in the blank: Every adult who lives in the village and whose name is on the voters' list is a member of the Gram _____, the meeting of all such people.**  _(code fill-in-the-blank, from sentence 2)_
   - A) Zila
   - B) Panchayat
   - C) Sabha  ✅
   - D) Parishad
   - source: "Every adult who lives in the village and whose name is on the voters' list is a member of the Gram Sabha, the meeting of all such people."
3. **Fill in the blank: It also carries out _____ schemes for employment and housing.**  _(code fill-in-the-blank, from sentence 8)_
   - A) adult
   - B) government  ✅
   - C) whose
   - D) sarpanch
   - source: "It also carries out government schemes for employment and housing."

**Held back: 4**

- RED, answer **Sabha**, sentence 2: "Every adult who lives in the village and whose name is on the voters' list is a member of the Gram Sabha, the meeting of all such people."
  - draft "Sabha"  [stem_question_mark, stem_no_answer_leak]
  - draft "Sabha"  [stem_question_mark, stem_no_answer_leak]
  - draft "Sabha"  [stem_question_mark, stem_no_answer_leak]
- RED, answer **government**, sentence 8: "It also carries out government schemes for employment and housing."
  - draft "What is carried out by the Ganga river?"  [stem_in_passage, stem_answers_to_key]  → answered back: "employment and housing"
  - draft "What is carried out by the sentence?"  [stem_in_passage, stem_answers_to_key]  → answered back: "employment and housing"
  - draft "What does the sentence "It also carries out government schemes for employment and housing" refer to?"  [stem_no_answer_leak, stem_readability]
- RED, answer **sarpanch**, sentence 10: "At its meetings, villagers can question the sarpanch about how money was spent and can suggest new work."
  - draft "At its meetings, villagers can question the sarpanch about how money was spent and can suggest new work."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "At its meetings, villagers can question the sarpanch about how money was spent and can suggest new work."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "At the meetings, villagers can question the sarpanch about how money was spent and can suggest new work."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
- AMBER, answer **elected**, sentence 4: "They are elected for five years."
  - draft "What is the main function of the sentence?"  [stem_in_passage, stem_answers_to_key]  → answered back: "to serve as a representative of the people."
  - draft "What is the main action of the sentence?"  [stem_in_passage]  → answered back: "elected"
  - draft "What do they do for five years?"  [stem_answers_to_key]  → answered back: "they serve as members of the government"
  - options: discussed | reserved | elected | member

## civ_secularism
*subject civics, class 8, style abstract-concept* · OK: 221 words · 15.3 s

**Summary**
- [model rewrite] The state doesn't have an official religion.
- [model rewrite] The goal is to make sure that no religious group dominates another, and that members of the same religion don't dominate each other, and that the state doesn't force any religion on people.

**Shown to the student: 3**  (1 written by the model, 2 fill-in-the-blank by code)

1. **What is India called?**  _(model, from sentence 1)_
   - A) practice
   - B) practise
   - C) festival
   - D) country  ✅
   - source: "India is a secular country."
2. **Fill in the blank: The aim of all this is to make sure that no religious group dominates another, that members of the same religion do not dominate each other, and that the _____ does not force any religion on people.**  _(code fill-in-the-blank, from sentence 10)_
   - A) Sikhs
   - B) State  ✅
   - C) Indian
   - D) Constitution
   - source: "The aim of all this is to make sure that no religious group dominates another, that members of the same religion do not dominate each other, and that the State does not force any religion on people."
3. **Fill in the blank: This means that it usually stays away from religious matters, but it can step in when a religious practice goes against the rights guaranteed by the _____.**  _(code fill-in-the-blank, from sentence 6)_
   - A) State
   - B) India
   - C) Sikhs
   - D) Constitution  ✅
   - source: "This means that it usually stays away from religious matters, but it can step in when a religious practice goes against the rights guaranteed by the Constitution."

**Held back: 4**

- RED, answer **State**, sentence 10: "The aim of all this is to make sure that no religious group dominates another, that members of the same religion do not dominate each other, and that the State does not force any religion on people."
  - draft "What is the main aim of the sentence?"  [stem_in_passage, stem_answers_to_key]  → answered back: "to promote religious harmony between different religions"
  - draft "What is the main aim of the sentence?"  [stem_in_passage, stem_answers_to_key]  → answered back: "to promote religious harmony between different religions"
  - draft "What is the main aim of the given sentence?"  [stem_in_passage, stem_answers_to_key]  → answered back: "to promote religious harmony and prevent religious domination"
- RED, answer **Constitution**, sentence 6: "This means that it usually stays away from religious matters, but it can step in when a religious practice goes against the rights guaranteed by the Constitution."
  - draft "Which of the following statements is correct regarding the Constitution?"  [stem_no_answer_leak, stem_in_passage]
  - draft "Which of the following is an example of a religious practice that can step in to protect rights guaranteed by the Constitution?"  [stem_length, stem_no_answer_leak]
  - draft "Which of the following is an example of freedom of religion?"  [stem_answers_to_key]  → answered back: "1. the Ganga river begins at the Gangotri glacier in the Himal"
- RED, answer **Sikhs**, sentence 9: "The law requires people riding two-wheelers to wear helmets, but Sikhs who wear turbans are allowed not to wear a helmet."
  - draft "The Sikhs are allowed to wear a helmet."  [stem_question_mark, stem_no_answer_leak]
  - draft "The law requires people riding two-wheelers to wear helmets, but Sikhs who wear turbans are allowed not to wear a helmet."  [stem_question_mark, stem_length, stem_no_answer_leak, stem_not_echo]
  - draft "The Sikhs are allowed not to wear a helmet, despite the law requiring them to."  [stem_question_mark, stem_no_answer_leak]
- RED, answer **official**, sentence 11: "In government schools, therefore, the celebration of a religious festival as an official school event is not allowed, but students are free to celebrate festivals at home."
  - draft "The celebration of a religious festival is not allowed in government schools."  [stem_question_mark]
  - draft "The celebration of a religious festival is not allowed in government schools."  [stem_question_mark]
  - draft "The government schools do not allow celebrations of religious festivals as official events."  [stem_question_mark, stem_no_answer_leak]

## civ_rights
*subject civics, class 8, style list-abbreviations* · OK: 216 words · 18.0 s

**Summary**
- [model rewrite] The Constitution of India gives every citizen basic rights called Fundamental Rights.
- [model rewrite] The right to freedom includes the right to speak, form associations, live anywhere, and work in any profession.
- [model rewrite] The right to freedom of religion lets everyone choose their religion.

**Shown to the student: 3**  (0 written by the model, 3 fill-in-the-blank by code)

1. **Fill in the blank: Everyone has _____ access to public places such as parks, wells and hotels.**  _(code fill-in-the-blank, from sentence 4)_
   - A) law
   - B) equal  ✅
   - C) misuse
   - D) citizen
   - source: "Everyone has equal access to public places such as parks, wells and hotels."
2. **Fill in the blank: The Right to Freedom of _____ allows everyone to follow the _____ of their choice.**  _(code fill-in-the-blank, from sentence 7)_
   - A) Constitutional
   - B) Equality
   - C) Fundamental
   - D) Religion  ✅
   - source: "The Right to Freedom of Religion allows everyone to follow the religion of their choice."
3. **Fill in the blank: The Right to _____ includes _____ of speech and expression, the _____ to form associations, the _____ to move to and live in any part of the country, and the _____ to practise any profession.**  _(code fill-in-the-blank, from sentence 5)_
   - A) Freedom  ✅
   - B) Constitution
   - C) Religion
   - D) Equality
   - source: "The Right to Freedom includes freedom of speech and expression, the freedom to form associations, the freedom to move to and live in any part of the country, and the freedom to practise any profession."

**Held back: 6**

- RED, answer **Religion**, sentence 7: "The Right to Freedom of Religion allows everyone to follow the religion of their choice."
  - draft "What is allowed by the Right to Freedom of Religion?"  [stem_no_answer_leak]
  - draft "What is allowed by the right to freedom of religion?"  [stem_no_answer_leak]
  - draft "What is the right to freedom of religion?"  [stem_no_answer_leak]
- RED, answer **Freedom**, sentence 5: "The Right to Freedom includes freedom of speech and expression, the freedom to form associations, the freedom to move to and live in any part of the country, and the freedom to practise any profession."
  - draft "What includes freedom of speech, expression, association, and profession?"  [stem_no_answer_leak]
  - draft "What includes freedom of speech, expression, association, movement, and profession?"  [stem_no_answer_leak]
  - draft "What does the Right to Freedom include?"  [stem_no_answer_leak]
- RED, answer **Constitution**, sentence 1: "The Constitution of India gives every citizen certain basic rights, called Fundamental Rights."
  - draft "What is given to every citizen in India by the Constitution of India?"  [stem_no_answer_leak]
  - draft "What is the name of the Constitution of India?"  [stem_no_answer_leak]
  - draft "What does the Constitution of India give every citizen?"  [stem_no_answer_leak]
- AMBER, answer **14**, sentence 6: "The Right against Exploitation forbids human trafficking, forced labour and the employment of children below 14 years in factories and mines."
  - draft "What is the minimum age for employment in factories and mines?"  [passed]  → answered back: "14 years"
- RED, answer **citizen**, sentence 9: "The Right to Constitutional Remedies allows a citizen to go directly to the courts if any of these rights is violated."
  - draft "What is the name of the right that allows a citizen to go directly to the courts if any of these rights is violated?"  [stem_length, stem_no_answer_leak]
  - draft "What is allowed by the Right to Constitutional Remedies?"  [stem_answers_to_key]  → answered back: "citizens can go directly to the courts if any of these rights is violated."
  - draft "What is the right to constitutional remedies called?"  [stem_answers_to_key]  → answered back: "constitutional remedies"
- RED, answer **Educational**, sentence 8: "Cultural and Educational Rights allow religious and linguistic minorities to set up their own schools to preserve their culture."
  - draft "What do educational rights allow?"  [stem_no_answer_leak]
  - draft "What do educational rights allow?"  [stem_no_answer_leak]
  - draft "What is allowed in education for minorities?"  [stem_answers_to_key]  → answered back: "education"

## civ_bill
*subject civics, class 8, style process-steps* · OK: 233 words · 18.7 s

**Summary**
- [model rewrite] A money bill, which deals with taxes and government spending, can be introduced only in the Lok Sabha, and the Rajya Sabha can only suggest changes to it within 14 days.
- [model rewrite] Once both houses have passed a bill, it goes to the president.

**Shown to the student: 3**  (0 written by the model, 3 fill-in-the-blank by code)

1. **Fill in the blank: Often the bill is sent to a small committee of _____, which studies it in detail and may hear the views of experts and the public.**  _(code fill-in-the-blank, from sentence 7)_
   - A) signs
   - B) stages
   - C) goes
   - D) members  ✅
   - source: "Often the bill is sent to a small committee of members, which studies it in detail and may hear the views of experts and the public."
2. **Fill in the blank: It is then debated, and members may _____ changes.**  _(code fill-in-the-blank, from sentence 6)_
   - A) suggest  ✅
   - B) proposal
   - C) committee
   - D) minister
   - source: "It is then debated, and members may suggest changes."
3. **Fill in the blank: Once both Houses have passed a bill, it is sent to the _____.**  _(code fill-in-the-blank, from sentence 12)_
   - A) Rajya
   - B) President  ✅
   - C) House
   - D) Sabha
   - source: "Once both Houses have passed a bill, it is sent to the President."

**Held back: 6**

- RED, answer **President**, sentence 12: "Once both Houses have passed a bill, it is sent to the President."
  - draft "Once both Houses have passed a bill, it is sent to the President."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "Once the bill is sent to the President, it is passed."  [stem_question_mark, stem_no_answer_leak]
  - draft "Once both Houses have passed a bill, it is sent to the President."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
- RED, answer **Sabha**, sentence 11: "A money bill, which deals with taxes and government spending, can be introduced only in the Lok Sabha, and the Rajya Sabha can only suggest changes to it within 14 days."
  - draft "The Rajya Sabha can only suggest changes to it within 14 days."  [stem_question_mark, stem_no_answer_leak]
  - draft "The Rajya Sabha can only suggest changes to it within 14 days."  [stem_question_mark, stem_no_answer_leak]
  - draft "The Rajya Sabha can only suggest changes to it within 14 days."  [stem_question_mark, stem_no_answer_leak]
- AMBER, answer **Parliament**, sentence 3: "A bill can be introduced by a minister or by any other member of Parliament."
  - draft "Which body of government can introduce a bill?"  [stem_in_passage]  → answered back: "Parliament"
  - draft "Which body of government can introduce a bill?"  [stem_in_passage]  → answered back: "Parliament"
  - draft "Which of the following is an example of a bill introduced in Parliament?"  [stem_no_answer_leak]
  - options: Sabha | President | Rajya | Parliament
- RED, answer **House**, sentence 5: "First the bill is read out and introduced in one House."
  - draft "Which house introduces the bill?"  [stem_no_answer_leak]
  - draft "Which house does the bill start in?"  [stem_no_answer_leak]
  - draft "Which house does the bill originate from?"  [stem_no_answer_leak]
- RED, answer **Houses**, sentence 10: "If the two Houses disagree, the President can call a joint sitting of both Houses to settle the matter."
  - draft "If the two Houses disagree, the President can call a joint sitting of both Houses to settle the matter."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "If the two Houses disagree, the President can call a joint sitting of both Houses to settle the matter."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "If the two Houses disagree, the President can call a joint sitting of both Houses to settle the matter."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
- RED, answer **law**, sentence 2: "A proposal for a new law is called a bill."
  - draft "What is called a bill?"  [stem_answers_to_key]  → answered back: "a proposal"
  - draft "What is called a bill?"  [stem_answers_to_key]  → answered back: "a proposal"
  - draft "What is called a bill?"  [stem_answers_to_key]  → answered back: "a proposal"

## eco_unemployment
*subject economics, class 9, style story-concept* · OK: 222 words · 20.1 s

**Summary**
- [model rewrite] The plot needs only two people to do all the work of plowing, sowing, and harvesting.
- [model rewrite] Lakshmi's cousin works on other people's farms during the harvest, but then has no job for four months.

**Shown to the student: 3**  (1 written by the model, 2 fill-in-the-blank by code)

1. **What is common in Indian agriculture?**  _(model, from sentence 7)_
   - A) land  ✅
   - B) grain
   - C) plot
   - D) village
   - source: "It is common in Indian agriculture, where many families share small pieces of land."
2. **Fill in the blank: Lakshmi's family owns a small plot of land in a village in _____.**  _(code fill-in-the-blank, from sentence 1)_
   - A) Rural
   - B) Employment
   - C) Bihar  ✅
   - D) Gandhi
   - source: "Lakshmi's family owns a small plot of land in a village in Bihar."
3. **Fill in the blank: In the _____ between, there is little to do, and many workers sit idle.**  _(code fill-in-the-blank, from sentence 10)_
   - A) months  ✅
   - B) pieces
   - C) faces
   - D) depends
   - source: "In the months between, there is little to do, and many workers sit idle."

**Held back: 5**

- RED, answer **National**, sentence 15: "To create more work, the government runs schemes such as the Mahatma Gandhi National Rural Employment Guarantee Act, which promises 100 days of paid work in a year to rural households."
  - draft "The government runs schemes such as the Mahatma Gandhi National Rural Employment Guarantee Act, which promises 100 days of paid work in a year to rural households."  [stem_question_mark, stem_length, stem_no_answer_leak, stem_not_echo]
  - draft "The government runs schemes such as the Mahatma Gandhi National Rural Employment Guarantee Act, which promises 100 days of paid work in a year to rural households."  [stem_question_mark, stem_length, stem_no_answer_leak, stem_not_echo]
  - draft "The government runs schemes called the Mahatma Gandhi National Rural Employment Guarantee Act."  [stem_question_mark, stem_no_answer_leak]
- AMBER, answer **unemployment**, sentence 12: "Lakshmi's cousin, who works on other people's farms during the harvest and then has no work for four months, faces seasonal unemployment."
  - draft "What is the main issue facing Lakshmi's cousin?"  [stem_in_passage]  → answered back: "unemployment"
  - draft "What is the main issue faced by Lakshmi's cousin?"  [stem_in_passage]  → answered back: "unemployment"
  - draft "What is the situation faced by Lakshmi's cousin?"  [stem_in_passage]  → answered back: "unemployment"
  - options: unemployment | family | plot | village
- RED, answer **village**, sentence 3: "But five members of the family work on it, because there is no other work for them in the village."
  - draft "The village has no other work for the family."  [stem_question_mark, stem_no_answer_leak]
  - draft "The family works in the village."  [stem_question_mark, stem_no_answer_leak]
  - draft "The village has no other work for the family."  [stem_question_mark, stem_no_answer_leak]
- AMBER, answer **harvesting**, sentence 2: "The plot needs only two people to do all the work of ploughing, sowing and harvesting."
  - draft "What is the main task of the plot?"  [stem_in_passage]  → answered back: "ploughing, sowing and harvesting"
  - draft "What is the main task of the plot?"  [stem_in_passage]  → answered back: "ploughing, sowing and harvesting"
  - draft "What is the main activity that the plot needs to do?"  [stem_in_passage]  → answered back: "ploughing, sowing and harvesting"
  - options: seasonal | months | land | harvesting
- RED, answer **farm**, sentence 4: "If three of them stopped working on the farm, the amount of grain produced would stay the same."
  - draft "If three of them stopped working on the farm, the amount of grain produced would stay the same."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "If three of them stopped working on the farm, the amount of grain produced would stay the same."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "If three of them stopped working on the farm, the amount of grain produced would stay the same."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]

## eco_money
*subject economics, class 10, style concept-example* · OK: 222 words · 22.0 s

**Summary**
- [model rewrite] Long ago, before money was used, people used to trade goods directly for other goods.
- [model rewrite] The shoemaker can sell his shoes for money and use that money to buy wheat from any farmer.
- [model rewrite] People keep money in banks as deposits.

**Shown to the student: 3**  (3 written by the model, 0 fill-in-the-blank by code)

1. **Which person is using money to buy wheat?**  _(model, from sentence 8)_
   - A) coincidence
   - B) farmer  ✅
   - C) imagine
   - D) difficult
   - source: "The shoemaker can sell his shoes to anyone for money, and then use that money to buy wheat from any farmer."
2. **Which country issues paper notes and coins?**  _(model, from sentence 11)_
   - source: "Today, we use paper notes and coins issued by the Reserve Bank of India on behalf of the government."
3. **What is the main thing that a shoemaker wants to do?**  _(model, from sentence 3)_
   - A) farmer
   - B) directly
   - C) wheat  ✅
   - D) difficult
   - source: "Imagine a shoemaker who wants to sell shoes and buy wheat."

**Held back: 3**

- RED, answer **deposits**, sentence 13: "People also keep money in banks as deposits."
  - draft "What is money kept in banks as? deposits"  [stem_question_mark, stem_no_answer_leak]
  - draft "What is kept in banks as deposits by people?"  [stem_no_answer_leak]
  - draft "What are people keeping in banks as deposits?"  [stem_no_answer_leak]
- RED, answer **coins**, sentence 10: "Over history, many things have been used as money, including grains, cattle, shells, and coins of gold, silver and copper."
  - draft "What has been used as money throughout history?"  [stem_answers_to_key]  → answered back: "grains, cattle, shells, and coins of gold, silver and copper"
  - draft "What has been used as money throughout history?"  [stem_answers_to_key]  → answered back: "grains, cattle, shells, and coins of gold, silver and copper"
  - draft "What has been used as money historically?"  [stem_answers_to_key]  → answered back: "grains, cattle, shells, and coins of gold, silver and copper"
- RED, answer **buy**, sentence 5: "This is called the double coincidence of wants: what one person wishes to sell is exactly what the other wishes to buy."
  - draft "What is the double coincidence of wants?"  [stem_answers_to_key]  → answered back: "double coincidence of wants"
  - draft "What is the double coincidence of wants?"  [stem_answers_to_key]  → answered back: "double coincidence of wants"
  - draft "What is the double coincidence of wants?"  [stem_answers_to_key]  → answered back: "double coincidence of wants"

## eco_shg
*subject economics, class 10, style problem-solution-numbers* · OK: 231 words · 21.6 s

**Summary**
- [model rewrite] Yes, members can get small loans from the group to meet their needs, and the group decides on the purpose, amount, and repayment schedule.
- [model rewrite] After a year or two, the group can get a loan from a bank.

**Shown to the student: 3**  (0 written by the model, 3 fill-in-the-blank by code)

1. **Fill in the blank: The interest charged is far lower than that of a _____.**  _(code fill-in-the-blank, from sentence 9)_
   - A) sold
   - B) group
   - C) moneylender  ✅
   - D) women
   - source: "The interest charged is far lower than that of a moneylender."
2. **Fill in the blank: The bank lends to the group as a whole, without collateral, because the _____ are responsible for repaying together.**  _(code fill-in-the-blank, from sentence 11)_
   - A) moneylenders
   - B) businesses
   - C) members  ✅
   - D) households
   - source: "The bank lends to the group as a whole, without collateral, because the members are responsible for repaying together."
3. **Fill in the blank: After a year or two of regular saving and repayment, the group becomes eligible for a loan from a _____.**  _(code fill-in-the-blank, from sentence 10)_
   - A) bank  ✅
   - B) month
   - C) interest
   - D) poor
   - source: "After a year or two of regular saving and repayment, the group becomes eligible for a loan from a bank."

**Held back: 6**

- AMBER, answer **bank**, sentence 10: "After a year or two of regular saving and repayment, the group becomes eligible for a loan from a bank."
  - draft "Which institution provides loans to groups?"  [stem_in_passage]  → answered back: "bank"
  - draft "Which of the following is a bank?"  [stem_no_answer_leak, stem_in_passage]
  - draft "Which organization provides the loans?"  [stem_in_passage, stem_readability]  → answered back: "bank"
  - options: bank | month | interest | poor
- RED, answer **repayment**, sentence 8: "Members can take small loans from the group to meet their needs, and the group decides the purpose, the amount and the repayment schedule."
  - draft "The group decides the purpose, the amount, and the repayment schedule."  [stem_question_mark, stem_no_answer_leak]
  - draft "The group decides the purpose, the amount, and the repayment schedule."  [stem_question_mark, stem_no_answer_leak]
  - draft "The repayment schedule is decided by the group."  [stem_question_mark, stem_no_answer_leak]
- RED, answer **SHGs**, sentence 4: "Self Help Groups, or SHGs, were formed to solve this problem."
  - draft "What groups were formed to solve this problem?"  [stem_answers_to_key]  → answered back: "Self Help Groups"
  - draft "What groups were formed to solve this problem?"  [stem_answers_to_key]  → answered back: "Self Help Groups"
  - draft "What are SHGs called?"  [stem_no_answer_leak]
- RED, answer **poor**, sentence 2: "Banks ask for collateral, such as land or a building, that can be sold if the loan is not repaid, and many poor people have nothing to offer."
  - draft "The poor people offer nothing to banks."  [stem_question_mark, stem_no_answer_leak]
  - draft "The poor people offer nothing to banks in return for collateral."  [stem_question_mark, stem_no_answer_leak]
  - draft "The poor people offer nothing to banks in exchange for collateral."  [stem_question_mark, stem_no_answer_leak]
- RED, answer **women**, sentence 12: "With such loans, women have started small businesses such as tailoring, poultry and making pickles."
  - draft "With such loans, women have started small businesses such as tailoring, poultry, and making pickles."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "With such loans, women have started small businesses such as tailoring, poultry, and making pickles."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "With such loans, women have started small businesses such as tailoring, poultry, and making pickles."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
- RED, answer **month**, sentence 3: "They are forced to borrow from moneylenders, who may charge interest as high as five per cent a month."
  - draft "What is the name of the person who is forced to borrow from moneylenders?"  [stem_answers_to_key]  → answered back: "the person"
  - draft "What is the rate of interest charged by moneylenders?"  [stem_answers_to_key]  → answered back: "five per cent"
  - draft "What is the monthly interest rate charged by moneylenders?"  [stem_readability, stem_answers_to_key]  → answered back: "five per cent"

## env_waste
*subject environment, class 6, style practical-advice* · OK: 228 words · 20.3 s

**Summary**
- [model rewrite] Every day, every household throws away some waste.
- [model rewrite] In many towns, the waste is collected by municipal workers and goes to low-lying open areas called landfills.
- [model rewrite] Kitchen waste like peels and leftovers is called biodegradable waste because tiny plants in the soil can break it down.

**Shown to the student: 3**  (2 written by the model, 1 fill-in-the-blank by code)

1. **What are the low-lying open areas called?**  _(model, from sentence 3)_
   - A) toys
   - B) flies
   - C) landfills  ✅
   - D) mountains
   - source: "In many towns, the waste is collected by municipal workers and taken to low-lying open areas called landfills."
2. **What can be melted and reused?**  _(model, from sentence 12)_
   - A) household
   - B) metal  ✅
   - C) vegetable
   - D) leftover
   - source: "Paper can be made into new paper, and glass and metal can be melted and reused."
3. **Fill in the blank: Burning _____ releases harmful gases.**  _(code fill-in-the-blank, from sentence 15)_
   - A) metal
   - B) soil
   - C) leftover
   - D) plastic  ✅
   - source: "Burning plastic releases harmful gases."

**Held back: 4**

- RED, answer **soil**, sentence 6: "Kitchen waste such as peels and leftover food is called biodegradable waste, because tiny organisms in the soil can break it down."
  - draft "The term for biodegradable waste is soil."  [stem_question_mark, stem_no_answer_leak]
  - draft "The term for biodegradable waste is soil."  [stem_question_mark, stem_no_answer_leak]
  - draft "The answer is: soil."  [stem_question_mark, stem_no_answer_leak, stem_in_passage]
- RED, answer **bag**, sentence 16: "The best way to deal with plastic is to reduce its use: carry a cloth bag to the market and refuse what you do not need."
  - draft "To deal with plastic, the best way is to carry a cloth bag to the market and refuse what you do not need."  [stem_question_mark, stem_length, stem_no_answer_leak]
  - draft "To deal with plastic, the best way is to carry a cloth bag to the market and refuse what you do not need."  [stem_question_mark, stem_length, stem_no_answer_leak]
  - draft "To deal with plastic, one can carry a cloth bag to the market and refuse what you do not need."  [stem_question_mark, stem_no_answer_leak]
- RED, answer **broken**, sentence 2: "Vegetable peels, leftover food, paper, plastic bags, bottles and broken toys all end up in the dustbin."
  - draft "What ends up in the dustbin?"  [stem_answers_to_key]  → answered back: "vegetable peels, paper, plastic bags, bottles, and broken toys."
  - draft "What ends up in the dustbin?"  [stem_answers_to_key]  → answered back: "vegetable peels, paper, plastic bags, bottles, and broken toys."
  - draft "What ends up in the dustbin?"  [stem_answers_to_key]  → answered back: "vegetable peels, paper, plastic bags, bottles, and broken toys."
- RED, answer **throws**, sentence 1: "Every day, every household throws away some waste."
  - draft "Every household throws away some waste every day."  [stem_question_mark, stem_no_answer_leak]
  - draft "Every household throws away some waste every day."  [stem_question_mark, stem_no_answer_leak]
  - draft "Every household throws away some waste every day."  [stem_question_mark, stem_no_answer_leak]

## env_solar
*subject environment, class 8, style numbers-heavy* · OK: 232 words · 18.2 s

**Summary**
- [model rewrite] The sun is the main source of energy, and solar energy can be turned into electricity using solar panels.
- [model rewrite] A solar panel has many solar cells, usually made of silicon.

**Shown to the student: 3**  (2 written by the model, 1 fill-in-the-blank by code)

1. **What is used to turn solar energy into electricity?**  _(model, from sentence 1)_
   - A) receives
   - B) panels  ✅
   - C) costs
   - D) units
   - source: "The Sun is the main source of energy for the Earth, and solar energy can be turned directly into electricity using solar panels."
2. **What is the main part of a solar panel?**  _(model, from sentence 2)_
   - A) units
   - B) cells  ✅
   - C) receives
   - D) gases
   - source: "A solar panel is made of many solar cells, usually made of silicon."
3. **Fill in the blank: A rooftop solar system of 1 kilowatt needs about 10 square metres of roof space and can produce about 4 units of electricity on a _____ day, which is enough to run a few lights, fans and a television in a small home.**  _(code fill-in-the-blank, from sentence 6)_
   - A) directly
   - B) electric
   - C) sunny  ✅
   - D) source
   - source: "A rooftop solar system of 1 kilowatt needs about 10 square metres of roof space and can produce about 4 units of electricity on a sunny day, which is enough to run a few lights, fans and a television in a small home."

**Held back: 4**

- RED, answer **India**, sentence 10: "The village of Dharnai in Bihar became one of the first in India to run entirely on a solar micro-grid in 2014."
  - draft "In which country did the village of Dharnai become one of the first in India to run entirely on a solar micro-grid in 2014?"  [stem_length, stem_no_answer_leak, stem_not_echo, stem_readability]
  - draft "In which country did the village of Dharnai become one of the first in India to run entirely on a solar micro-grid in 2014?"  [stem_length, stem_no_answer_leak, stem_not_echo, stem_readability]
  - draft "In which country did the village of Dharnai become one of the first in India to run entirely on a solar micro-grid in 2014?"  [stem_length, stem_no_answer_leak, stem_not_echo, stem_readability]
- RED, answer **electricity**, sentence 8: "However, solar panels produce no electricity at night and less on cloudy days, so the extra electricity produced during the day is stored in batteries or sent to the main electricity grid."
  - draft "What is stored in batteries or sent to the main electricity grid during the day?"  [stem_no_answer_leak]
  - draft "What is stored in batteries or sent to the main electricity grid?"  [stem_no_answer_leak]
  - draft "What is stored in batteries or sent to the main electricity grid?"  [stem_no_answer_leak]
- RED, answer **costs**, sentence 7: "Solar energy does not produce smoke or harmful gases, and the sunlight itself costs nothing."
  - draft "Solar energy does not produce smoke or harmful gases, and the sunlight itself costs nothing."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "Solar energy costs nothing."  [stem_question_mark, stem_no_answer_leak, stem_readability]
  - draft "Solar energy costs nothing."  [stem_question_mark, stem_no_answer_leak, stem_readability]
- RED, answer **produces**, sentence 3: "When sunlight falls on a solar cell, it produces a small electric current."
  - draft "When sunlight falls on a solar cell, it produces a small electric current."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "When sunlight falls on a solar cell, it produces a small electric current."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
  - draft "When sunlight falls on a solar cell, it produces a small electric current."  [stem_question_mark, stem_no_answer_leak, stem_not_echo]
