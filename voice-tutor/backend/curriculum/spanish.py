from __future__ import annotations
from curriculum.types import Lesson, VocabItem, QuizQuestion, LessonStep, RoleplayScenario
from typing import Optional

LESSON_GREETINGS = Lesson(
    id="lesson-greetings",
    title="Greetings and Introductions",
    objective="Learn how to greet people, introduce yourself, and ask how someone is doing in Spanish.",
    vocabulary=[
        VocabItem("hola", "hello / hi", "OH-lah — the H is completely silent"),
        VocabItem("buenos días", "good morning", "BWEH-nos DEE-ahs — stress the first syllable of each word"),
        VocabItem("buenas tardes", "good afternoon", "BWEH-nahs TAR-des — used from noon until sunset"),
        VocabItem("buenas noches", "good evening / good night", "BWEH-nahs NOH-ches — CH sounds like English CH"),
        VocabItem("¿cómo te llamas?", "what is your name?", "KOH-moh teh YAH-mahs — double-L sounds like Y in most dialects"),
        VocabItem("me llamo", "my name is", "meh YAH-moh — literally 'I call myself'"),
        VocabItem("mucho gusto", "nice to meet you", "MOO-choh GOOS-toh — G is soft before U"),
        VocabItem("¿cómo estás?", "how are you? (informal)", "KOH-moh ehs-TAHS — stress the last syllable of estás"),
        VocabItem("¿cómo está usted?", "how are you? (formal)", "KOH-moh ehs-TAH oos-TED — use with strangers or elders"),
        VocabItem("estoy bien", "I am fine / well", "ehs-TOY BYEN — bien rhymes with 'yen'"),
        VocabItem("estoy mal", "I am not well / bad", "ehs-TOY mahl — honest answer when things are rough"),
        VocabItem("más o menos", "more or less / so-so", "mahs oh MEH-nos — a very common casual answer"),
        VocabItem("hasta luego", "see you later", "AHS-tah LWEH-goh — luego means 'later'"),
        VocabItem("adiós", "goodbye", "ah-DYOHS — stress the last syllable"),
    ],
    grammarNotes=[
        "Formal vs informal address: Use 'tú' (informal) with friends, peers, and children. Use 'usted' (formal) with strangers, elders, or in professional settings. '¿Cómo estás?' is informal; '¿Cómo está usted?' is formal.",
        "Verb ESTAR vs SER: Both mean 'to be' but serve different purposes. ESTAR describes temporary states — 'Estoy bien' (I am well right now). SER describes permanent identity — 'Soy María' (I am María). Never mix them up for self-introductions vs. describing how you feel.",
    ],
    exampleDialogues=[
        {"spanish": "— ¡Hola! Buenos días. ¿Cómo te llamas?\n— Me llamo Carlos. ¿Y tú?\n— Me llamo Ana. Mucho gusto.\n— Mucho gusto, Ana. ¿Cómo estás?\n— Estoy bien, gracias. ¿Y tú?\n— Más o menos.", "english": "— Hello! Good morning. What is your name?\n— My name is Carlos. And you?\n— My name is Ana. Nice to meet you.\n— Nice to meet you, Ana. How are you?\n— I am fine, thank you. And you?\n— So-so."},
        {"spanish": "— Buenas tardes. ¿Cómo está usted?\n— Estoy bien, gracias. ¿Y usted?\n— Muy bien. Hasta luego.\n— Adiós.", "english": "— Good afternoon. How are you? (formal)\n— I am well, thank you. And you?\n— Very well. See you later.\n— Goodbye."},
    ],
    steps=[
        LessonStep(
            id="greet-objective",
            type="objective",
            agentScript="Welcome to Lesson 1: Greetings and Introductions! By the end of this lesson you'll know how to greet people at any time of day, introduce yourself, and ask how someone is doing — all in Spanish. I'll give you the English first, then the Spanish. Ready?",
            expectsUserResponse=False,
        ),
        LessonStep(
            id="greet-explain-basic",
            type="explanation",
            agentScript="Let's start with 'hello'. In Spanish, 'hello' is 'hola' — the H is completely silent, so you say OH-lah. For time-of-day greetings: 'good morning' is 'buenos días', 'good afternoon' is 'buenas tardes', and 'good evening' is 'buenas noches'. Now try saying 'good morning' in Spanish.",
            expectsUserResponse=True,
        ),
        LessonStep(
            id="greet-practice-hello",
            type="practice",
            agentScript="Nice! It's 9 in the morning and you walk into a shop. How do you greet the shopkeeper in Spanish?",
            expectsUserResponse=True,
        ),
        LessonStep(
            id="greet-explain-names",
            type="explanation",
            agentScript="Now, introductions. To ask 'what is your name?' in Spanish you say '¿cómo te llamas?' — KOH-moh teh YAH-mahs. The double-L sounds like a Y. To answer 'my name is', you say 'me llamo' and then your name. For example, I would say 'me llamo Sofia'. Now try asking me: what is your name — in Spanish.",
            expectsUserResponse=True,
        ),
        LessonStep(
            id="greet-practice-names",
            type="practice",
            agentScript="Good! Now introduce yourself — tell me 'my name is' followed by your name, in Spanish.",
            expectsUserResponse=True,
        ),
        LessonStep(
            id="greet-explain-howru",
            type="explanation",
            agentScript="Next: 'how are you?' With friends you say '¿cómo estás?' — stress the last syllable: ehs-TAHS. Formally, it's '¿cómo está usted?'. The common answers are: 'I'm well' is 'estoy bien', 'I'm not well' is 'estoy mal', and 'so-so' is 'más o menos'. Now answer this in Spanish: how are you?",
            expectsUserResponse=True,
        ),
        LessonStep(
            id="greet-example-dialogue",
            type="example",
            agentScript="Let's put it all together. I'll greet you in Spanish and you respond. Ready? In English I'm saying: Hello, good morning. What is your name? — Now say that back to me in Spanish, then introduce yourself.",
            expectsUserResponse=True,
        ),
        LessonStep(
            id="greet-check",
            type="check",
            agentScript="Almost done! Last one: how do you say 'goodbye' and 'see you later' in Spanish? Two different phrases.",
            expectsUserResponse=True,
        ),
    ],
    quizQuestions=[
        QuizQuestion(
            id="greet-q1",
            type="translation_en_es",
            prompt="How do you say 'Good morning' in Spanish?",
            expectedAnswer="buenos días",
            acceptedVariants=["buenos dias", "buenos días"],
            targetVocab="buenos días",
        ),
        QuizQuestion(
            id="greet-q2",
            type="translation_es_en",
            prompt="What does '¿cómo te llamas?' mean in English?",
            expectedAnswer="what is your name",
            acceptedVariants=["what's your name", "what is your name?", "what are you called"],
            targetVocab="¿cómo te llamas?",
        ),
        QuizQuestion(
            id="greet-q3",
            type="spoken_response",
            prompt="Tell me your name in Spanish using the correct phrase.",
            expectedAnswer="me llamo",
            acceptedVariants=["me llamo [name]", "mi nombre es"],
            targetVocab="me llamo",
        ),
        QuizQuestion(
            id="greet-q4",
            type="translation_en_es",
            prompt="How do you say 'I am fine' in Spanish?",
            expectedAnswer="estoy bien",
            acceptedVariants=["estoy bien", "estoy muy bien"],
            targetVocab="estoy bien",
        ),
        QuizQuestion(
            id="greet-q5",
            type="translation_es_en",
            prompt="What does 'más o menos' mean?",
            expectedAnswer="more or less",
            acceptedVariants=["so-so", "more or less", "not great not bad", "okay"],
            targetVocab="más o menos",
        ),
        QuizQuestion(
            id="greet-q6-listen",
            type="listening",
            prompt="Listen to this phrase and tell me what it means: 'buenas noches'",
            expectedAnswer="good evening",
            acceptedVariants=["good night", "good evening", "good night / good evening"],
            targetVocab="buenas noches",
        ),
        QuizQuestion(
            id="greet-q7-listen",
            type="listening",
            prompt="Listen and translate: 'mucho gusto'",
            expectedAnswer="nice to meet you",
            acceptedVariants=["nice to meet you", "pleased to meet you", "my pleasure"],
            targetVocab="mucho gusto",
        ),
    ],
)

LESSON_NUMBERS = Lesson(
    id="lesson-numbers",
    title="Numbers and Basic Shopping",
    objective="Count from 1 to 20 in Spanish and use numbers in a basic shopping conversation.",
    vocabulary=[
        VocabItem("uno", "one", "OO-noh — becomes 'un' before masculine nouns, 'una' before feminine"),
        VocabItem("dos", "two", "dohs — rhymes with 'those'"),
        VocabItem("tres", "three", "trehs — roll the R lightly"),
        VocabItem("cuatro", "four", "KWAH-troh — QU sounds like K"),
        VocabItem("cinco", "five", "SEEN-koh — C before I sounds like S"),
        VocabItem("seis", "six", "sehs — one syllable"),
        VocabItem("siete", "seven", "SYEH-teh — two syllables"),
        VocabItem("ocho", "eight", "OH-choh"),
        VocabItem("nueve", "nine", "NWEH-beh — V sounds like B in Spanish"),
        VocabItem("diez", "ten", "dyehs — Z sounds like S in Latin America"),
        VocabItem("once", "eleven", "ON-seh"),
        VocabItem("doce", "twelve", "DOH-seh"),
        VocabItem("trece", "thirteen", "TREH-seh"),
        VocabItem("catorce", "fourteen", "kah-TOR-seh"),
        VocabItem("quince", "fifteen", "KEEN-seh"),
        VocabItem("dieciséis", "sixteen", "dyeh-see-SEHS — three syllables"),
        VocabItem("diecisiete", "seventeen", "dyeh-see-SYEH-teh"),
        VocabItem("dieciocho", "eighteen", "dyeh-see-OH-choh"),
        VocabItem("diecinueve", "nineteen", "dyeh-see-NWEH-beh"),
        VocabItem("veinte", "twenty", "BEYN-teh — V sounds like B"),
        VocabItem("¿cuánto cuesta?", "how much does it cost?", "KWAHN-toh KWEHS-tah — essential shopping phrase"),
        VocabItem("cuesta", "it costs", "KWEHS-tah — from the verb costar"),
        VocabItem("quiero", "I want", "KYEH-roh — direct but acceptable in shops"),
        VocabItem("quisiera", "I would like", "kee-SYEH-rah — more polite than quiero"),
        VocabItem("por favor", "please", "por fah-VOR — always use this in shops"),
        VocabItem("gracias", "thank you", "GRAH-syahs"),
        VocabItem("de nada", "you're welcome", "deh NAH-dah — literally 'of nothing'"),
        VocabItem("¿tiene...?", "do you have...?", "TYEH-neh — from tener, to have"),
        VocabItem("no tengo", "I don't have", "noh TEHN-goh — shopkeeper's reply"),
        VocabItem("lo siento", "I'm sorry", "loh SYEHN-toh — used when apologizing"),
    ],
    grammarNotes=[
        "Gender agreement with numbers: 'uno' changes based on noun gender. Before a masculine noun: 'un euro' (one euro). Before a feminine noun: 'una manzana' (one apple). For all other numbers (dos, tres, etc.) there is no gender change.",
        "Formal register in shops: Always use 'quisiera' (I would like) rather than 'quiero' (I want) when shopping — it sounds more polite. Add 'por favor' at the end of any request.",
    ],
    exampleDialogues=[
        {"spanish": "— Buenos días. ¿Tiene manzanas?\n— Sí, tenemos. ¿Cuántas quiere?\n— Quisiera cinco, por favor. ¿Cuánto cuesta?\n— Cuesta tres euros.\n— Gracias.\n— De nada.", "english": "— Good morning. Do you have apples?\n— Yes, we do. How many do you want?\n— I would like five, please. How much does it cost?\n— It costs three euros.\n— Thank you.\n— You're welcome."},
    ],
    steps=[
        LessonStep(
            id="num-objective",
            type="objective",
            agentScript="Welcome to Lesson 2: Numbers and Basic Shopping! I'll teach you each number by saying its English value first, then the Spanish word. By the end you'll count to 20 and hold a basic shopping conversation.",
            expectsUserResponse=False,
        ),
        LessonStep(
            id="num-explain-1-10",
            type="explanation",
            agentScript="Let's do 1 to 10. One is 'uno', two is 'dos', three is 'tres', four is 'cuatro', five is 'cinco'. Quick tip — in Spanish the letter V sounds like B, so nine, which is 'nueve', sounds like NWEH-beh. Now say 1 through 5 in Spanish.",
            expectsUserResponse=True,
        ),
        LessonStep(
            id="num-practice-1-10",
            type="practice",
            agentScript="Six is 'seis', seven is 'siete', eight is 'ocho', nine is 'nueve', ten is 'diez'. Now count 6 through 10 in Spanish.",
            expectsUserResponse=True,
        ),
        LessonStep(
            id="num-explain-11-20",
            type="explanation",
            agentScript="Eleven through fifteen: eleven is 'once', twelve is 'doce', thirteen is 'trece', fourteen is 'catorce', fifteen is 'quince'. Now say eleven through fifteen in Spanish.",
            expectsUserResponse=True,
        ),
        LessonStep(
            id="num-practice-11-20",
            type="practice",
            agentScript="Sixteen through twenty follow the pattern 'dieci' plus the unit — sixteen is 'dieciséis', seventeen 'diecisiete', eighteen 'dieciocho', nineteen 'diecinueve', twenty is 'veinte'. Count 16 to 20 in Spanish.",
            expectsUserResponse=True,
        ),
        LessonStep(
            id="num-explain-shopping",
            type="explanation",
            agentScript="Now let's shop. 'How much does it cost?' in Spanish is '¿cuánto cuesta?' 'It costs' is 'cuesta' — so 'it costs five euros' is 'cuesta cinco euros'. 'I would like' is 'quisiera' — always use this in shops, it's polite. Try asking: how much does it cost? — in Spanish.",
            expectsUserResponse=True,
        ),
        LessonStep(
            id="num-dialogue-practice",
            type="practice",
            agentScript="Roleplay time. You're at a market. In Spanish, say: I would like twelve apples, please. How much does it cost?",
            expectsUserResponse=True,
        ),
        LessonStep(
            id="num-check",
            type="check",
            agentScript="Last question: 'I want' in Spanish is 'quiero', and 'I would like' is 'quisiera'. Why would you choose 'quisiera' when shopping?",
            expectsUserResponse=True,
        ),
    ],
    quizQuestions=[
        QuizQuestion(
            id="num-q1",
            type="translation_en_es",
            prompt="How do you say the number 7 in Spanish?",
            expectedAnswer="siete",
            acceptedVariants=["siete"],
            targetVocab="siete",
        ),
        QuizQuestion(
            id="num-q2",
            type="translation_en_es",
            prompt="How do you say 15 in Spanish?",
            expectedAnswer="quince",
            acceptedVariants=["quince"],
            targetVocab="quince",
        ),
        QuizQuestion(
            id="num-q3",
            type="translation_es_en",
            prompt="What does '¿cuánto cuesta?' mean?",
            expectedAnswer="how much does it cost",
            acceptedVariants=["how much is it", "how much does it cost?", "what does it cost"],
            targetVocab="¿cuánto cuesta?",
        ),
        QuizQuestion(
            id="num-q4",
            type="spoken_response",
            prompt="You want to buy 3 items politely. Say: 'I would like three, please' in Spanish.",
            expectedAnswer="quisiera tres, por favor",
            acceptedVariants=["quisiera tres por favor", "quisiera tres"],
            targetVocab="quisiera",
        ),
        QuizQuestion(
            id="num-q5",
            type="translation_en_es",
            prompt="How do you say 'thank you' in Spanish?",
            expectedAnswer="gracias",
            acceptedVariants=["gracias"],
            targetVocab="gracias",
        ),
        QuizQuestion(
            id="num-q6-listen",
            type="listening",
            prompt="Listen to this phrase and tell me what it means: '¿cuánto cuesta?'",
            expectedAnswer="how much does it cost",
            acceptedVariants=["how much is it", "how much does it cost?", "what does it cost"],
            targetVocab="¿cuánto cuesta?",
        ),
        QuizQuestion(
            id="num-q7-listen",
            type="listening",
            prompt="Listen and translate: 'de nada'",
            expectedAnswer="you're welcome",
            acceptedVariants=["you're welcome", "no problem", "not at all", "of nothing"],
            targetVocab="de nada",
        ),
    ],
)

LESSON_RESTAURANT = Lesson(
    id="lesson-restaurant",
    title="At a Restaurant",
    objective="Order food and drinks, ask for recommendations, and pay the bill at a Spanish-speaking restaurant.",
    vocabulary=[
        VocabItem("la mesa", "the table", "lah MEH-sah", gender="feminine", exampleSentence="Una mesa para dos, por favor."),
        VocabItem("el menú", "the menu", "ehl meh-NOO", gender="masculine", exampleSentence="¿Me trae el menú, por favor?"),
        VocabItem("la carta", "the menu (alternative word)", "lah KAR-tah", gender="feminine", exampleSentence="¿Puedo ver la carta?"),
        VocabItem("el camarero", "the waiter (male)", "ehl kah-mah-REH-roh", gender="masculine"),
        VocabItem("la camarera", "the waitress (female)", "lah kah-mah-REH-rah", gender="feminine"),
        VocabItem("quiero pedir", "I want to order", "KYEH-roh peh-DEER — pedir means to order/ask for"),
        VocabItem("¿qué recomienda?", "what do you recommend?", "keh reh-koh-MYEHN-dah — great way to start"),
        VocabItem("el plato principal", "the main course", "ehl PLAH-toh preen-see-PAL", gender="masculine"),
        VocabItem("el postre", "dessert", "ehl POHS-treh", gender="masculine", exampleSentence="¿Qué hay de postre?"),
        VocabItem("la bebida", "the drink", "lah beh-BEE-dah", gender="feminine", exampleSentence="¿Qué bebidas tienen?"),
        VocabItem("sin", "without", "seen — useful for dietary restrictions", exampleSentence="sin gluten, sin carne"),
        VocabItem("con", "with", "kon", exampleSentence="con salsa, con hielo"),
        VocabItem("¿está incluido el servicio?", "is the service charge included?", "ehs-TAH een-kloo-EE-doh ehl sehr-VEE-syoh"),
        VocabItem("la cuenta, por favor", "the bill, please", "lah KWEHN-tah por fah-VOR — the most important restaurant phrase"),
        VocabItem("¡buen provecho!", "enjoy your meal!", "bwehn proh-VEH-choh — said by staff when bringing food"),
    ],
    grammarNotes=[
        "Noun gender — el vs la: Spanish nouns are masculine (el) or feminine (la). There is no strict rule but common patterns help: nouns ending in -o are often masculine (el menú, el postre), nouns ending in -a are often feminine (la mesa, la carta, la bebida). Learning gender with the noun from the start is the best strategy.",
        "Conditional for polite requests — quisiera vs quiero: 'Quiero' (I want) is grammatically correct but can sound abrupt. 'Quisiera' (I would like) uses the imperfect subjunctive as a conditional and is the polite register for restaurants. Always prefer 'quisiera' when ordering.",
        "Subjunctive hint — quiero que sea: When making special requests, you may hear 'quiero que sea sin sal' (I want it to be without salt). The 'que sea' triggers the subjunctive mood — a verb form used after expressions of wanting, doubting, or emotion.",
    ],
    exampleDialogues=[
        {"spanish": "— Buenas noches. Una mesa para dos, por favor.\n— Por aquí, por favor.\n— Gracias. ¿Me trae la carta?\n— Aquí tiene. ¿Qué desean pedir?\n— ¿Qué recomienda usted?\n— El plato principal del día está muy bueno.\n— Quisiera el plato principal, por favor. Sin cebolla.\n— Perfecto. ¿Y para beber?\n— Agua, por favor.\n— ¡Buen provecho!\n— La cuenta, por favor.", "english": "— Good evening. A table for two, please.\n— This way, please.\n— Thank you. Could you bring the menu?\n— Here you are. What would you like to order?\n— What do you recommend?\n— Today's main course is very good.\n— I would like the main course, please. Without onion.\n— Perfect. And to drink?\n— Water, please.\n— Enjoy your meal!\n— The bill, please."},
    ],
    steps=[
        LessonStep(
            id="rest-objective",
            type="objective",
            agentScript="Welcome to Lesson 3: At a Restaurant! You'll learn to get a table, order food, make special requests, and ask for the bill — all in Spanish. English first, Spanish second, every time.",
            expectsUserResponse=False,
        ),
        LessonStep(
            id="rest-vocabulary",
            type="explanation",
            agentScript="Let's start with key words. 'The table' in Spanish is 'la mesa'. 'The menu' is 'el menú'. 'The waiter' is 'el camarero' and 'the waitress' is 'la camarera'. 'The bill' is 'la cuenta'. Notice 'la' is feminine and 'el' is masculine — the article comes first. Say these three: the table, the menu, the bill — in Spanish.",
            expectsUserResponse=True,
        ),
        LessonStep(
            id="rest-gender-drill",
            type="practice",
            agentScript="Quick gender drill — I'll say a restaurant word in English, you give me the Spanish with the correct article. First: dessert.",
            expectsUserResponse=True,
        ),
        LessonStep(
            id="rest-ordering",
            type="explanation",
            agentScript="Now, ordering. 'I would like' is 'quisiera' — always use this in a restaurant, it's polite. 'Without' is 'sin', so 'without gluten' is 'sin gluten'. 'What do you recommend?' is '¿qué recomienda?' Try it — in Spanish, say: I would like the main course without onion.",
            expectsUserResponse=True,
        ),
        LessonStep(
            id="rest-dialogue",
            type="practice",
            agentScript="Roleplay: you've sat down at the restaurant. I'm the waiter and I'll ask in Spanish what you want. Respond in Spanish — order something and mention what you don't want.",
            expectsUserResponse=True,
        ),
        LessonStep(
            id="rest-bill",
            type="example",
            agentScript="After the meal you need the bill. 'The bill, please' in Spanish is 'la cuenta, por favor'. You can also ask 'is service included?' which is '¿está incluido el servicio?'. How do you ask for the bill in Spanish?",
            expectsUserResponse=True,
        ),
        LessonStep(
            id="rest-check",
            type="check",
            agentScript="Last question: 'I want' is 'quiero' and 'I would like' is 'quisiera'. Why is 'quisiera' the better choice in a restaurant?",
            expectsUserResponse=True,
        ),
    ],
    quizQuestions=[
        QuizQuestion(
            id="rest-q1",
            type="translation_en_es",
            prompt="How do you say 'the bill, please' in Spanish?",
            expectedAnswer="la cuenta, por favor",
            acceptedVariants=["la cuenta por favor", "la cuenta, por favor"],
            targetVocab="la cuenta, por favor",
        ),
        QuizQuestion(
            id="rest-q2",
            type="translation_es_en",
            prompt="What does '¡buen provecho!' mean?",
            expectedAnswer="enjoy your meal",
            acceptedVariants=["enjoy your meal!", "bon appétit", "good appetite", "enjoy"],
            targetVocab="¡buen provecho!",
        ),
        QuizQuestion(
            id="rest-q3",
            type="spoken_response",
            prompt="Order the main course politely in Spanish, without garlic.",
            expectedAnswer="quisiera el plato principal sin ajo, por favor",
            acceptedVariants=["quisiera el plato principal sin ajo", "quisiera el plato del día sin ajo, por favor"],
            targetVocab="quisiera",
        ),
        QuizQuestion(
            id="rest-q4",
            type="translation_es_en",
            prompt="What does 'sin' mean in 'sin cebolla'?",
            expectedAnswer="without",
            acceptedVariants=["without"],
            targetVocab="sin",
        ),
        QuizQuestion(
            id="rest-q5",
            type="translation_en_es",
            prompt="How do you ask 'What do you recommend?' in Spanish?",
            expectedAnswer="¿qué recomienda?",
            acceptedVariants=["que recomienda", "¿qué recomienda?", "qué recomienda usted"],
            targetVocab="¿qué recomienda?",
        ),
        QuizQuestion(
            id="rest-q6",
            type="spoken_response",
            prompt="A table for two, please — say it in Spanish.",
            expectedAnswer="una mesa para dos, por favor",
            acceptedVariants=["una mesa para dos por favor", "mesa para dos, por favor"],
            targetVocab="la mesa",
        ),
        QuizQuestion(
            id="rest-q7-listen",
            type="listening",
            prompt="Listen to this phrase and tell me what it means: '¡buen provecho!'",
            expectedAnswer="enjoy your meal",
            acceptedVariants=["enjoy your meal!", "bon appétit", "good appetite", "enjoy"],
            targetVocab="¡buen provecho!",
        ),
        QuizQuestion(
            id="rest-q8-listen",
            type="listening",
            prompt="Listen and translate: 'sin cebolla'",
            expectedAnswer="without onion",
            acceptedVariants=["without onion", "no onion"],
            targetVocab="sin",
        ),
    ],
)

LESSONS: dict[str, Lesson] = {
    LESSON_GREETINGS.id: LESSON_GREETINGS,
    LESSON_NUMBERS.id: LESSON_NUMBERS,
    LESSON_RESTAURANT.id: LESSON_RESTAURANT,
}

ROLEPLAY_SCENARIOS: dict[str, RoleplayScenario] = {
    "roleplay-restaurant": RoleplayScenario(
        id="roleplay-restaurant",
        title="At a Restaurant",
        description="You are a customer at a Spanish restaurant. Sofia plays the waiter. Order food, ask what's recommended, and request the bill.",
        characterContext="You are Miguel, a friendly waiter at a tapas restaurant in Madrid. Speak mostly Spanish with short English hints in parentheses when the learner seems stuck. Keep each line to one or two sentences.",
        openingLine="¡Buenas noches! Bienvenido. ¿Mesa para cuántas personas?",
        openingHint="(Good evening! Welcome. Table for how many?)",
        targetVocab=["quisiera", "la cuenta, por favor", "¿qué recomienda?", "sin", "el menú"],
    ),
    "roleplay-market": RoleplayScenario(
        id="roleplay-market",
        title="At the Market",
        description="You are shopping at a Spanish market. Sofia plays the vendor. Ask prices, buy items, and use polite phrases.",
        characterContext="You are Ana, a cheerful market vendor selling fruit and vegetables. Speak mostly Spanish with English hints as needed.",
        openingLine="¡Buenos días! ¿En qué le puedo ayudar?",
        openingHint="(Good morning! How can I help you?)",
        targetVocab=["¿cuánto cuesta?", "quisiera", "gracias", "por favor", "de nada"],
    ),
    "roleplay-greeting": RoleplayScenario(
        id="roleplay-greeting",
        title="Meeting Someone New",
        description="You have just arrived at a Spanish language school. Sofia plays a fellow student. Introduce yourself and make small talk.",
        characterContext="You are Carlos, a friendly Spanish student who is enthusiastic and encouraging. Keep your lines short so the learner can respond.",
        openingLine="¡Hola! Buenos días. ¿Eres nuevo aquí?",
        openingHint="(Hello! Good morning. Are you new here?)",
        targetVocab=["me llamo", "mucho gusto", "¿cómo estás?", "estoy bien", "hasta luego"],
    ),
}


def get_lesson(lesson_id: str) -> Optional[Lesson]:
    return LESSONS.get(lesson_id)


def list_lessons() -> list[Lesson]:
    return list(LESSONS.values())


def get_roleplay_scenario(scenario_id: str) -> Optional[RoleplayScenario]:
    return ROLEPLAY_SCENARIOS.get(scenario_id)


def list_roleplay_scenarios() -> list[RoleplayScenario]:
    return list(ROLEPLAY_SCENARIOS.values())
