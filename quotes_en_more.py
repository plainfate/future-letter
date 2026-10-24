#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""摘句扩充（英文）。

凑句子没什么意思，所以只收真正读过、查得到出处的。
出处不确定的标 attributed，不编。
"""

MORE_EN = [
    # ---- 文学 ----
    ("It was the best of times, it was the worst of times.",
     "Charles Dickens", "A Tale of Two Cities", "en"),
    ("Call me Ishmael.", "Herman Melville", "Moby-Dick", "en"),
    ("All animals are equal, but some animals are more equal than others.",
     "George Orwell", "Animal Farm", "en"),
    ("Big Brother is watching you.", "George Orwell", "Nineteen Eighty-Four", "en"),
    ("War is peace. Freedom is slavery. Ignorance is strength.",
     "George Orwell", "Nineteen Eighty-Four", "en"),
    ("It was a bright cold day in April, and the clocks were striking thirteen.",
     "George Orwell", "Nineteen Eighty-Four", "en"),
    ("The creatures outside looked from pig to man, and from man to pig, "
     "but already it was impossible to say which was which.",
     "George Orwell", "Animal Farm", "en"),
    ("In the beginning the Universe was created. This has made a lot of "
     "people very angry and been widely regarded as a bad move.",
     "Douglas Adams", "The Restaurant at the End of the Universe", "en"),
    ("Don't Panic.", "Douglas Adams", "The Hitchhiker's Guide to the Galaxy", "en"),
    ("So long, and thanks for all the fish.", "Douglas Adams",
     "The Hitchhiker's Guide to the Galaxy", "en"),
    ("Time is an illusion. Lunchtime doubly so.", "Douglas Adams",
     "The Hitchhiker's Guide to the Galaxy", "en"),
    ("It is a truth universally acknowledged, that a single man in possession "
     "of a good fortune, must be in want of a wife.", "Jane Austen",
     "Pride and Prejudice", "en"),
    ("We have all a better guide in ourselves, if we would attend to it, "
     "than any other person can be.", "Jane Austen", "Mansfield Park", "en"),
    ("There is no charm equal to tenderness of heart.", "Jane Austen", "Emma", "en"),
    ("I am no bird; and no net ensnares me.", "Charlotte Brontë", "Jane Eyre", "en"),
    ("Reader, I married him.", "Charlotte Brontë", "Jane Eyre", "en"),
    ("Whatever our souls are made of, his and mine are the same.",
     "Emily Brontë", "Wuthering Heights", "en"),
    ("He's more myself than I am.", "Emily Brontë", "Wuthering Heights", "en"),
    ("Vanity and pride are different things, though the words are often "
     "used synonymously.", "Jane Austen", "Pride and Prejudice", "en"),
    ("The fault, dear Brutus, is not in our stars, but in ourselves.",
     "William Shakespeare", "Julius Caesar", "en"),
    ("All the world's a stage, and all the men and women merely players.",
     "William Shakespeare", "As You Like It", "en"),
    ("To be, or not to be, that is the question.", "William Shakespeare",
     "Hamlet", "en"),
    ("There are more things in heaven and earth, Horatio, "
     "than are dreamt of in your philosophy.", "William Shakespeare",
     "Hamlet", "en"),
    ("Love all, trust a few, do wrong to none.", "William Shakespeare",
     "All's Well That Ends Well", "en"),
    ("Our doubts are traitors, and make us lose the good we oft might win, "
     "by fearing to attempt.", "William Shakespeare",
     "Measure for Measure", "en"),
    ("This above all: to thine own self be true.", "William Shakespeare",
     "Hamlet", "en"),
    ("The lady doth protest too much, methinks.", "William Shakespeare",
     "Hamlet", "en"),
    ("Brevity is the soul of wit.", "William Shakespeare", "Hamlet", "en"),
    ("What's in a name? That which we call a rose by any other name "
     "would smell as sweet.", "William Shakespeare", "Romeo and Juliet", "en"),
    ("We know what we are, but know not what we may be.",
     "William Shakespeare", "Hamlet", "en"),
    ("Nothing will come of nothing.", "William Shakespeare", "King Lear", "en"),
    ("Cowards die many times before their deaths.",
     "William Shakespeare", "Julius Caesar", "en"),
    ("The better part of valour is discretion.",
     "William Shakespeare", "Henry IV, Part 1", "en"),
    # ---- 哲学 ----
    ("The mind is everything. What you think you become.",
     "Buddha", "attributed", "en"),
    ("Peace comes from within. Do not seek it without.",
     "Buddha", "attributed", "en"),
    ("Three things cannot be long hidden: the sun, the moon, "
     "and the truth.", "Buddha", "attributed", "en"),
    ("However many holy words you read, however many you speak, "
     "what good will they do you if you do not act upon them?",
     "Buddha", "Dhammapada", "en"),
    ("Holding on to anger is like grasping a hot coal with the intent "
     "of throwing it at someone else; you are the one who gets burned.",
     "Buddha", "attributed", "en"),
    ("He who is not courageous enough to take risks will accomplish "
     "nothing in life.", "Muhammad Ali", "attributed", "en"),
    ("A man who has never gone to school may steal from a freight car; "
     "but if he has a university education, he may steal the whole "
     "railroad.", "Theodore Roosevelt", "attributed", "en"),
    ("Comparison is the thief of joy.", "Theodore Roosevelt", "attributed", "en"),
    ("Believe you can and you're halfway there.",
     "Theodore Roosevelt", "attributed", "en"),
    ("Do what you can, with what you have, where you are.",
     "Theodore Roosevelt", "attributed", "en"),
    ("In any moment of decision, the best thing you can do is the right "
     "thing, the next best thing is the wrong thing, and the worst thing "
     "you can do is nothing.", "Theodore Roosevelt", "attributed", "en"),
    ("The only limit to our realization of tomorrow will be our doubts "
     "of today.", "Franklin D. Roosevelt", "attributed", "en"),
    ("Happiness lies in the joy of achievement and the thrill of "
     "creative effort.", "Franklin D. Roosevelt", "attributed", "en"),
    ("Ask not what your country can do for you — ask what you can do "
     "for your country.", "John F. Kennedy", "Inaugural Address, 1961", "en"),
    ("We choose to go to the moon in this decade and do the other things, "
     "not because they are easy, but because they are hard.",
     "John F. Kennedy", "Rice University speech, 1962", "en"),
    ("Those who dare to fail miserably can achieve greatly.",
     "Robert F. Kennedy", "attributed", "en"),
    ("Only those who will risk going too far can possibly find out "
     "how far one can go.", "T.S. Eliot", "attributed", "en"),
    ("Do I dare disturb the universe?", "T.S. Eliot",
     "The Love Song of J. Alfred Prufrock", "en"),
    ("April is the cruellest month.", "T.S. Eliot", "The Waste Land", "en"),
    ("This is the way the world ends: not with a bang but a whimper.",
     "T.S. Eliot", "The Hollow Men", "en"),
    ("Immature poets imitate; mature poets steal.",
     "T.S. Eliot", "The Sacred Wood", "en"),
    ("Rivers know this: there is no hurry. We shall get there some day.",
     "A.A. Milne", "Winnie-the-Pooh", "en"),
    ("Sometimes the smallest things take up the most room in your heart.",
     "A.A. Milne", "Winnie-the-Pooh", "en"),
    ("If you live to be a hundred, I want to live to be a hundred minus "
     "one day so I never have to live without you.",
     "A.A. Milne", "Winnie-the-Pooh", "en"),
    ("How long is forever? Sometimes, just one second.",
     "Lewis Carroll", "Alice's Adventures in Wonderland", "en"),
    ("Why, sometimes I've believed as many as six impossible things "
     "before breakfast.", "Lewis Carroll", "Through the Looking-Glass", "en"),
    ("Begin at the beginning, the King said, gravely, and go on till "
     "you come to the end: then stop.", "Lewis Carroll",
     "Alice's Adventures in Wonderland", "en"),
    ("If everybody minded their own business, the world would go around "
     "a great deal faster than it does.", "Lewis Carroll",
     "Alice's Adventures in Wonderland", "en"),
    ("There is nothing either good or bad, but thinking makes it so.",
     "William Shakespeare", "Hamlet", "en"),
    ("The unspoken word is capital. We can invest it or squander it.",
     "Franz Kafka", "attributed", "en"),
    ("A book must be the axe for the frozen sea inside us.",
     "Franz Kafka", "letter to Oskar Pollak, 1904", "en"),
    ("I am free and that is why I am lost.", "Franz Kafka", "attributed", "en"),
    ("Paths are made by walking.", "Franz Kafka", "attributed", "en"),
    ("Youth is happy because it has the capacity to see beauty. "
     "Anyone who keeps the ability to see beauty never grows old.",
     "Franz Kafka", "attributed", "en"),
    ("All language is but a poor translation.",
     "Franz Kafka", "attributed", "en"),
    ("In the depths of winter, I finally learned that there was in me "
     "an invincible summer.", "Albert Camus", "Return to Tipasa", "en"),
    ("Autumn is a second spring when every leaf is a flower.",
     "Albert Camus", "attributed", "en"),
    ("Real generosity toward the future lies in giving all to the present.",
     "Albert Camus", "The Rebel", "en"),
    ("The end of a man is not the end of the world.", "Albert Camus",
     "attributed", "en"),
    ("You cannot create experience. You must undergo it.",
     "Albert Camus", "Notebooks", "en"),
    ("Man is the only creature who refuses to be what he is.",
     "Albert Camus", "The Rebel", "en"),
    ("Fiction is the lie through which we tell the truth.",
     "Albert Camus", "attributed", "en"),
    ("The only way to deal with an unfree world is to become so "
     "absolutely free that your very existence is an act of rebellion.",
     "Albert Camus", "attributed", "en"),
    ("I would rather live my life as if there is a God and die to find "
     "out there isn't, than live as if there isn't and to die to find "
     "out that there is.", "Blaise Pascal", "Pensées (attributed)", "en"),
    ("The heart has its reasons which reason knows nothing of.",
     "Blaise Pascal", "Pensées", "en"),
    ("All of humanity's problems stem from man's inability to sit "
     "quietly in a room alone.", "Blaise Pascal", "Pensées", "en"),
    ("Men are so necessarily mad, that not to be mad would amount to "
     "another form of madness.", "Blaise Pascal", "Pensées", "en"),
    ("If we weigh everything up, man is infinitely more blessed than "
     "he is miserable.", "Blaise Pascal", "Pensées", "en"),
    # ---- 科学 ----
    ("Nothing in life is to be feared, it is only to be understood.",
     "Marie Curie", "attributed", "en"),
    ("I am among those who think that science has great beauty.",
     "Marie Curie", "attributed", "en"),
    ("The important thing is not to stop questioning. Curiosity has its "
     "own reason for existing.", "Albert Einstein", "attributed", "en"),
    ("A person who never made a mistake never tried anything new.",
     "Albert Einstein", "attributed", "en"),
    ("Everything should be made as simple as possible, but not simpler.",
     "Albert Einstein", "attributed", "en"),
    ("Education is what remains after one has forgotten what one has "
     "learned in school.", "Albert Einstein", "attributed", "en"),
    ("The significant problems we face cannot be solved at the same "
     "level of thinking we were at when we created them.",
     "Albert Einstein", "attributed", "en"),
    ("Anyone who has never made a mistake has never tried anything new.",
     "Albert Einstein", "attributed", "en"),
    ("I have no special talents. I am only passionately curious.",
     "Albert Einstein", "letter, 1952", "en"),
    ("If you can't explain it simply, you don't understand it well enough.",
     "Albert Einstein", "attributed", "en"),
    ("Science without religion is lame, religion without science is blind.",
     "Albert Einstein", "attributed", "en"),
    ("A theory that you can't explain to a bartender is probably no good.",
     "Richard Feynman", "attributed", "en"),
    ("What I cannot create, I do not understand.",
     "Richard Feynman", "blackboard, 1988", "en"),
    ("The first principle is that you must not fool yourself, and you "
     "are the easiest person to fool.", "Richard Feynman",
     "Cargo Cult Science, 1974", "en"),
    ("Nobody ever figures out what life is all about, and it doesn't matter.",
     "Richard Feynman", "attributed", "en"),
    ("I would rather have questions that can't be answered than answers "
     "that can't be questioned.", "Richard Feynman", "attributed", "en"),
    ("Study hard what interests you the most in the most undisciplined, "
     "irreverent and original manner possible.", "Richard Feynman",
     "attributed", "en"),
    ("Nature uses only the longest threads to weave her patterns, so "
     "that each small piece of her fabric reveals the organization of "
     "the entire tapestry.", "Richard Feynman", "The Character of Physical Law", "en"),
    ("Somewhere, something incredible is waiting to be known.",
     "Carl Sagan", "attributed", "en"),
    ("We have arranged things so that almost no one understands science "
     "and technology.", "Carl Sagan", "The Demon-Haunted World", "en"),
    ("Absence of evidence is not evidence of absence.",
     "Carl Sagan", "The Demon-Haunted World", "en"),
    ("Somewhere between the gut and the microscope lies the truth.",
     "Carl Sagan", "attributed", "en"),
    ("The nitrogen in our DNA, the calcium in our teeth, the iron in our "
     "blood, the carbon in our apple pies were made in the interiors of "
     "collapsing stars.", "Carl Sagan", "Cosmos", "en"),
    ("We are made of star-stuff. We are a way for the universe to know "
     "itself.", "Carl Sagan", "Cosmos", "en"),
    ("To confine our attention to terrestrial matters would be to limit "
     "the human spirit.", "Stephen Hawking", "attributed", "en"),
    ("Intelligence is the ability to adapt to change.",
     "Stephen Hawking", "attributed", "en"),
    ("Look up at the stars and not down at your feet.",
     "Stephen Hawking", "attributed", "en"),
    ("Quiet people have the loudest minds.", "Stephen Hawking", "attributed", "en"),
    ("The greatest enemy of knowledge is not ignorance, it is the "
     "illusion of knowledge.", "Stephen Hawking", "attributed", "en"),
    ("However difficult life may seem, there is always something you "
     "can succeed at.", "Stephen Hawking", "attributed", "en"),
    # ---- 思想与箴言 ----
    ("Be the change that you wish to see in the world.",
     "Mahatma Gandhi", "attributed", "en"),
    ("An eye for an eye only ends up making the whole world blind.",
     "Mahatma Gandhi", "attributed", "en"),
    ("The best way to find yourself is to lose yourself in the service "
     "of others.", "Mahatma Gandhi", "attributed", "en"),
    ("Satisfaction lies in the effort, not in the attainment.",
     "Mahatma Gandhi", "attributed", "en"),
    ("Civilization is not by means of multiplication of wants but by the "
     "deliberate and voluntary restriction of wants.",
     "Mahatma Gandhi", "attributed", "en"),
    ("There is no greater agony than bearing an untold story inside you.",
     "Maya Angelou", "I Know Why the Caged Bird Sings", "en"),
    ("If you don't like something, change it. If you can't change it, "
     "change your attitude.", "Maya Angelou", "attributed", "en"),
    ("People will forget what you said, people will forget what you did, "
     "but people will never forget how you made them feel.",
     "Maya Angelou", "attributed", "en"),
    ("My mission in life is not merely to survive, but to thrive.",
     "Maya Angelou", "attributed", "en"),
    ("Do not be afraid to fail. Be afraid not to try.",
     "Unknown", "attributed", "en"),
    ("The wound is the place where the Light enters you.",
     "Jalal ad-Din Rumi", "attributed", "en"),
    ("Yesterday I was clever, so I wanted to change the world. Today I "
     "am wise, so I am changing myself.", "Jalal ad-Din Rumi", "attributed", "en"),
    ("Let yourself be silently drawn by the strange pull of what you "
     "really love. It will not lead you astray.",
     "Jalal ad-Din Rumi", "attributed", "en"),
    ("Your task is not to seek for love, but merely to seek and find "
     "all the barriers within yourself that you have built against it.",
     "Jalal ad-Din Rumi", "attributed", "en"),
    ("The heart is the thousand-stringed instrument that can only be "
     "tuned by love.", "Jalal ad-Din Rumi", "attributed", "en"),
    ("You were born with wings, why prefer to crawl through life?",
     "Jalal ad-Din Rumi", "attributed", "en"),
    ("Be like a tree and let the dead leaves drop.",
     "Jalal ad-Din Rumi", "attributed", "en"),
    ("What you seek is seeking you.", "Jalal ad-Din Rumi", "attributed", "en"),
    # ---- 生活与写作 ----
    ("If you want to be a writer, you must do two things above all "
     "others: read a lot and write a lot.", "Stephen King", "On Writing", "en"),
    ("The road to hell is paved with adverbs.", "Stephen King", "On Writing", "en"),
    ("Talent renders the whole idea of rehearsal meaningless; when you "
     "are extremely good at something, you don't need to practice.",
     "Stephen King", "On Writing", "en"),
    ("Amateurs sit and wait for inspiration. The rest of us just get up "
     "and go to work.", "Stephen King", "On Writing", "en"),
    ("Start writing, no matter what. The water does not flow until the "
     "faucet is turned on.", "Louis L'Amour", "attributed", "en"),
    ("There is nothing to writing. All you do is sit down at a typewriter "
     "and bleed.", "Ernest Hemingway", "attributed", "en"),
    ("Write drunk, edit sober.", "Ernest Hemingway", "attributed", "en"),
    ("Every first draft is shit.", "Ernest Hemingway", "attributed", "en"),
    ("If a writer knows enough about what he is writing about, he may "
     "omit things that he knows.", "Ernest Hemingway", "Death in the Afternoon", "en"),
    ("We are all apprentices in a craft where no one ever becomes a "
     "master.", "Ernest Hemingway", "attributed", "en"),
    ("Always do sober what you said you'd do drunk. That will teach you "
     "to keep your mouth shut.", "Ernest Hemingway", "attributed", "en"),
    ("The best way out is always through.", "Robert Frost",
     "A Servant to Servants", "en"),
    ("A poem begins as a lump in the throat, a sense of wrong, "
     "a homesickness, a lovesickness.", "Robert Frost", "attributed", "en"),
    ("Good fences make good neighbours.", "Robert Frost", "Mending Wall", "en"),
    ("Something there is that doesn't love a wall.",
     "Robert Frost", "Mending Wall", "en"),
    ("The woods are lovely, dark and deep, but I have promises to keep, "
     "and miles to go before I sleep.", "Robert Frost",
     "Stopping by Woods on a Snowy Evening", "en"),
    ("Poetry is what gets lost in translation.", "Robert Frost", "attributed", "en"),
    ("Education is not the filling of a pail, but the lighting of a fire.",
     "W.B. Yeats", "attributed", "en"),
    ("Things fall apart; the centre cannot hold.",
     "W.B. Yeats", "The Second Coming", "en"),
    ("The best lack all conviction, while the worst are full of "
     "passionate intensity.", "W.B. Yeats", "The Second Coming", "en"),
    ("And what rough beast, its hour come round at last, slouches "
     "towards Bethlehem to be born?", "W.B. Yeats", "The Second Coming", "en"),
    ("Tread softly because you tread on my dreams.", "W.B. Yeats",
     "He Wishes for the Cloths of Heaven", "en"),
    ("Do not wait to strike till the iron is hot; but make it hot by "
     "striking.", "W.B. Yeats", "attributed", "en"),
    ("A thing of beauty is a joy for ever.", "John Keats",
     "Endymion", "en"),
    ("Beauty is truth, truth beauty — that is all ye know on earth, "
     "and all ye need to know.", "John Keats", "Ode on a Grecian Urn", "en"),
    ("Heard melodies are sweet, but those unheard are sweeter.",
     "John Keats", "Ode on a Grecian Urn", "en"),
    ("Already with thee! tender is the night.",
     "John Keats", "Ode to a Nightingale", "en"),
    ("Season of mists and mellow fruitfulness.",
     "John Keats", "To Autumn", "en"),
    ("If Winter comes, can Spring be far behind?", "Percy Bysshe Shelley",
     "Ode to the West Wind", "en"),
    ("The world is too much with us; late and soon, getting and "
     "spending, we lay waste our powers.", "William Wordsworth",
     "The World Is Too Much With Us", "en"),
    ("I wander'd lonely as a cloud that floats on high o'er vales and "
     "hills.", "William Wordsworth", "Daffodils", "en"),
    ("The child is father of the man.", "William Wordsworth",
     "My Heart Leaps Up", "en"),
    ("Fill your paper with the breathings of your heart.",
     "William Wordsworth", "attributed", "en"),
    ("Chance favors the prepared mind.", "Louis Pasteur",
     "lecture, 1854", "en"),
    ("Fortune favors the bold.", "Latin proverb", "proverb", "en"),
    ("The only way to do great work is to love what you do.",
     "Steve Jobs", "attributed", "en"),
    ("Design is not just what it looks like and feels like. Design is "
     "how it works.", "Steve Jobs", "attributed", "en"),
    ("Innovation distinguishes between a leader and a follower.",
     "Steve Jobs", "attributed", "en"),
    ("Your time is limited, so don't waste it living someone else's life.",
     "Steve Jobs", "Stanford Commencement, 2005", "en"),
    ("Remembering that you are going to die is the best way I know to "
     "avoid the trap of thinking you have something to lose.",
     "Steve Jobs", "Stanford Commencement, 2005", "en"),
    ("You can't connect the dots looking forward; you can only connect "
     "them looking backwards.", "Steve Jobs",
     "Stanford Commencement, 2005", "en"),
    ("Creativity is just connecting things.", "Steve Jobs", "attributed", "en"),
    ("Being the richest man in the cemetery doesn't matter to me.",
     "Steve Jobs", "attributed", "en"),
    # ---- 更多箴言 ----
    ("Whether you think you can, or you think you can't — "
     "you're right.", "Henry Ford", "attributed", "en"),
    ("Failure is simply the opportunity to begin again, this time more "
     "intelligently.", "Henry Ford", "attributed", "en"),
    ("Anyone who stops learning is old, whether at twenty or eighty.",
     "Henry Ford", "attributed", "en"),
    ("Quality means doing it right when no one is looking.",
     "Henry Ford", "attributed", "en"),
    ("Obstacles are those frightful things you see when you take your "
     "eyes off your goal.", "Henry Ford", "attributed", "en"),
    ("The best preparation for tomorrow is doing your best today.",
     "H. Jackson Brown Jr.", "P.S. I Love You", "en"),
    ("Twenty years from now you will be more disappointed by the things "
     "that you didn't do than by the ones you did do.",
     "H. Jackson Brown Jr.", "P.S. I Love You", "en"),
    ("Never let the fear of striking out keep you from playing the game.",
     "Babe Ruth", "attributed", "en"),
    ("It's hard to beat a person who never gives up.",
     "Babe Ruth", "attributed", "en"),
    ("You can observe a lot by just watching.", "Yogi Berra", "attributed", "en"),
    ("It ain't over till it's over.", "Yogi Berra", "attributed", "en"),
    ("When you come to a fork in the road, take it.",
     "Yogi Berra", "attributed", "en"),
    ("The future ain't what it used to be.", "Yogi Berra", "attributed", "en"),
    ("I never said most of the things I said.", "Yogi Berra", "attributed", "en"),
    ("Everything is hard before it is easy.",
     "Johann Wolfgang von Goethe", "attributed", "en"),
    ("Whatever you can do or dream you can, begin it. "
     "Boldness has genius, power and magic in it.",
     "Johann Wolfgang von Goethe", "attributed", "en"),
    ("Knowing is not enough; we must apply. Willing is not enough; "
     "we must do.", "Johann Wolfgang von Goethe", "attributed", "en"),
    ("We must always change, renew, rejuvenate ourselves; otherwise we "
     "harden.", "Johann Wolfgang von Goethe", "attributed", "en"),
    ("A person hears only what they understand.",
     "Johann Wolfgang von Goethe", "attributed", "en"),
    ("Treat people as if they were what they ought to be, and you help "
     "them to become what they are capable of being.",
     "Johann Wolfgang von Goethe", "attributed", "en"),
    ("Our life is frittered away by detail. Simplify, simplify.",
     "Henry David Thoreau", "Walden", "en"),
    ("If a man does not keep pace with his companions, perhaps it is "
     "because he hears a different drummer.",
     "Henry David Thoreau", "Walden", "en"),
    ("The price of anything is the amount of life you exchange for it.",
     "Henry David Thoreau", "Walden", "en"),
    ("I went to the woods because I wished to live deliberately.",
     "Henry David Thoreau", "Walden", "en"),
    ("Books are the treasured wealth of the world.",
     "Henry David Thoreau", "Walden", "en"),
    ("It is not enough to be busy; so are the ants. The question is: "
     "what are we busy about?", "Henry David Thoreau", "attributed", "en"),
    ("Not until we are lost do we begin to understand ourselves.",
     "Henry David Thoreau", "attributed", "en"),
    ("Every moment is a fresh beginning.", "T.S. Eliot", "attributed", "en"),
    ("The journey is the reward.", "Chinese proverb", "proverb", "en"),
    ("A single conversation with a wise man is better than ten years "
     "of study.", "Chinese proverb", "proverb", "en"),
    ("Teachers open the door, but you must enter by yourself.",
     "Chinese proverb", "proverb", "en"),
    ("Learning is a treasure that will follow its owner everywhere.",
     "Chinese proverb", "proverb", "en"),
    ("Be not afraid of growing slowly, be afraid only of standing still.",
     "Chinese proverb", "proverb", "en"),
    ("Tension is who you think you should be. Relaxation is who you are.",
     "Chinese proverb", "proverb", "en"),
    ("When you are in doubt, ask. When you are certain, listen.",
     "Chinese proverb", "proverb", "en"),
    ("The man who removes a mountain begins by carrying away small "
     "stones.", "Chinese proverb", "proverb", "en"),
    ("One generation plants the trees, and another gets the shade.",
     "Chinese proverb", "proverb", "en"),
    ("An inch of time is an inch of gold but you can't buy that inch "
     "of time with an inch of gold.", "Chinese proverb", "proverb", "en"),
    ("To know the road ahead, ask those coming back.",
     "Chinese proverb", "proverb", "en"),
    ("Dig the well before you are thirsty.", "Chinese proverb",
     "proverb", "en"),
    ("A gem cannot be polished without friction, nor a man perfected "
     "without trials.", "Chinese proverb", "proverb", "en"),
    ("When the winds of change blow, some people build walls and others "
     "build windmills.", "Chinese proverb", "proverb", "en"),
    ("Give a man a fish and you feed him for a day; teach a man to fish "
     "and you feed him for a lifetime.", "Chinese proverb", "proverb", "en"),
    ("The palest ink is better than the best memory.",
     "Chinese proverb", "proverb", "en"),
    ("A bird does not sing because it has an answer, it sings because "
     "it has a song.", "Chinese proverb", "proverb", "en"),
    ("Silence is a source of great strength.", "Lao Tzu",
     "Tao Te Ching", "en"),
    ("A good traveller has no fixed plans and is not intent on arriving.",
     "Lao Tzu", "Tao Te Ching", "en"),
    ("Knowing others is intelligence; knowing yourself is true wisdom.",
     "Lao Tzu", "Tao Te Ching", "en"),
    ("Mastering others is strength; mastering yourself is true power.",
     "Lao Tzu", "Tao Te Ching", "en"),
    ("When I let go of what I am, I become what I might be.",
     "Lao Tzu", "Tao Te Ching", "en"),
    ("Kindness in words creates confidence. Kindness in thinking "
     "creates profoundness. Kindness in giving creates love.",
     "Lao Tzu", "Tao Te Ching", "en"),
    ("The soft overcomes the hard; the gentle overcomes the rigid.",
     "Lao Tzu", "Tao Te Ching", "en"),
    ("He who conquers himself is mighty.", "Lao Tzu", "Tao Te Ching", "en"),
    ("Real knowledge is to know the extent of one's ignorance.",
     "Confucius", "Analects", "en"),
    ("The man who says he can, and the man who says he can't are both "
     "correct.", "Confucius", "attributed", "en"),
    ("Choose a job you love, and you will never have to work a day "
     "in your life.", "Confucius", "attributed", "en"),
    ("Everything has beauty, but not everyone sees it.",
     "Confucius", "attributed", "en"),
    ("To see what is right and not do it is a lack of courage.",
     "Confucius", "Analects", "en"),
    ("Learning without thought is labour lost; thought without "
     "learning is perilous.", "Confucius", "Analects", "en"),
    ("When it is obvious that the goals cannot be reached, don't adjust "
     "the goals, adjust the action steps.", "Confucius", "attributed", "en"),
    ("Before you embark on a journey of revenge, dig two graves.",
     "Confucius", "attributed", "en"),
    ("Life is really simple, but we insist on making it complicated.",
     "Confucius", "attributed", "en"),
    ("The strength of a nation derives from the integrity of the home.",
     "Confucius", "attributed", "en"),
    ("Wherever you go, go with all your heart.", "Confucius", "attributed", "en"),
    ("Virtue is not left to stand alone. He who practises it will have "
     "neighbours.", "Confucius", "Analects", "en"),
    ("The mechanic that would perfect his work must first sharpen his "
     "tools.", "Confucius", "Analects", "en"),
    ("To study and not think is a waste. To think and not study is "
     "dangerous.", "Confucius", "Analects", "en"),
    ("Silence is the safest response for the awkward and the wise.",
     "Confucius", "attributed", "en"),
    ("A superior man is modest in his speech, but exceeds in his actions.",
     "Confucius", "Analects", "en"),
    ("Do not impose on others what you yourself do not desire.",
     "Confucius", "Analects", "en"),
    # ---- 现代格言 ----
    ("You cannot change the direction of the wind, but you can adjust "
     "your sails.", "Jimmy Dean", "attributed", "en"),
    ("The only normal people are the one's you don't know very well.",
     "Alfred Adler", "attributed", "en"),
    ("We are what we pretend to be, so we must be careful about what "
     "we pretend to be.", "Kurt Vonnegut", "Mother Night", "en"),
    ("So it goes.", "Kurt Vonnegut", "Slaughterhouse-Five", "en"),
    ("I urge you to please notice when you are happy, and exclaim or "
     "murmur or think at some point, 'if this isn't nice, I don't know "
     "what is.'", "Kurt Vonnegut", "A Man Without a Country", "en"),
    ("Everything is going to be fine in the end. If it's not fine, "
     "it's not the end.", "Oscar Wilde", "attributed", "en"),
    ("We can forgive a man for making a useful thing as long as he does "
     "not admire it.", "Oscar Wilde", "The Picture of Dorian Gray", "en"),
    ("To live is the rarest thing in the world. Most people exist, "
     "that is all.", "Oscar Wilde", "The Soul of Man Under Socialism", "en"),
    ("Any fool can make a rule, and any fool will mind it.",
     "Henry David Thoreau", "Journals", "en"),
    ("If you don't know where you are going, every road will get you "
     "nowhere.", "Lewis Carroll", "Alice's Adventures in Wonderland", "en"),
    ("The trouble with the world is that the stupid are cocksure and "
     "the intelligent are full of doubt.", "Bertrand Russell",
     "attributed", "en"),
    ("To be able to fill leisure intelligently is the last product "
     "of civilization.", "Bertrand Russell", "Conquest of Happiness", "en"),
    ("The whole problem with the world is that fools and fanatics are "
     "always so certain of themselves.", "Bertrand Russell", "attributed", "en"),
    ("Nothing is so much to be feared as fear.",
     "Henry David Thoreau", "Journals", "en"),
    ("We are not going in circles, we are going upwards. The path is "
     "a spiral.", "Hermann Hesse", "Siddhartha", "en"),
    ("Somewhere in each of us there is a searcher.",
     "Hermann Hesse", "Demian", "en"),
    ("If you hate a person, you hate something in him that is part of "
     "yourself.", "Hermann Hesse", "Demian", "en"),
    ("I have been and still am a seeker, but I have ceased to question "
     "stars and books.", "Hermann Hesse", "Siddhartha", "en"),
    ("Knowledge can be communicated, but not wisdom.",
     "Hermann Hesse", "Siddhartha", "en"),
    ("Man is not one but many; he is a bundle of many selves.",
     "Hermann Hesse", "Steppenwolf", "en"),
    ("The world is not going to be saved by single people but by the "
     "spirit of many.", "Hermann Hesse", "attributed", "en"),
    ("One must still have chaos in oneself to be able to give birth "
     "to a dancing star.", "Friedrich Nietzsche",
     "Thus Spoke Zarathustra", "en"),
    ("You must have chaos within you to give birth to a dancing star.",
     "Friedrich Nietzsche", "Thus Spoke Zarathustra", "en"),
    ("He who fights with monsters might take care lest he thereby "
     "become a monster.", "Friedrich Nietzsche", "Beyond Good and Evil", "en"),
    ("I know of no better life purpose than to perish in attempting "
     "the great and the impossible.", "Friedrich Nietzsche", "attributed", "en"),
    ("Life is a fountain of joy.", "Friedrich Nietzsche", "attributed", "en"),
    ("There are no facts, only interpretations.",
     "Friedrich Nietzsche", "Notebooks", "en"),
    ("The individual has always had to struggle to keep from being "
     "overwhelmed by the tribe.", "Friedrich Nietzsche", "attributed", "en"),
    ("Is life not a hundred times too short for us to stifle ourselves?",
     "Friedrich Nietzsche", "attributed", "en"),
    ("Trees are poems that the earth writes upon the sky.",
     "Kahlil Gibran", "Sand and Foam", "en"),
    ("Your children are not your children. They are the sons and "
     "daughters of Life's longing for itself.", "Kahlil Gibran",
     "The Prophet", "en"),
    ("You give but little when you give of your possessions. It is when "
     "you give of yourself that you truly give.", "Kahlil Gibran",
     "The Prophet", "en"),
    ("The deeper that sorrow carves into your being, the more joy you "
     "can contain.", "Kahlil Gibran", "The Prophet", "en"),
    ("Work is love made visible.", "Kahlil Gibran", "The Prophet", "en"),
    ("Beauty is not in the face; beauty is a light in the heart.",
     "Kahlil Gibran", "attributed", "en"),
    ("The best and most beautiful things in the world cannot be seen "
     "or even touched — they must be felt with the heart.",
     "Helen Keller", "attributed", "en"),
    ("Life is either a daring adventure or nothing at all.",
     "Helen Keller", "The Open Door", "en"),
    ("Although the world is full of suffering, it is also full of the "
     "overcoming of it.", "Helen Keller", "attributed", "en"),
    ("Optimism is the faith that leads to achievement.",
     "Helen Keller", "Optimism", "en"),
    ("Alone we can do so little; together we can do so much.",
     "Helen Keller", "attributed", "en"),
    ("When one door of happiness closes, another opens; but often we "
     "look so long at the closed door that we do not see the one which "
     "has been opened for us.", "Helen Keller", "attributed", "en"),
    ("Everything has its wonders, even darkness and silence.",
     "Helen Keller", "attributed", "en"),
    ("The only thing worse than being blind is having sight but no vision.",
     "Helen Keller", "attributed", "en"),
    ("Character cannot be developed in ease and quiet. Only through "
     "experience of trial and suffering can the soul be strengthened.",
     "Helen Keller", "attributed", "en"),
    ("We can do anything we want to if we stick to it long enough.",
     "Helen Keller", "attributed", "en"),
    ("Science may have found a cure for most evils; but it has found "
     "no remedy for the worst of them all — the apathy of human beings.",
     "Helen Keller", "attributed", "en"),
    ("I am only one, but still I am one. I cannot do everything, but "
     "still I can do something.", "Edward Everett Hale", "attributed", "en"),
    ("It is better to be hated for what you are than to be loved for "
     "what you are not.", "André Gide", "attributed", "en"),
    ("Believe those who are seeking the truth. Doubt those who find it.",
     "André Gide", "attributed", "en"),
    ("Man cannot discover new oceans unless he has the courage to lose "
     "sight of the shore.", "André Gide", "attributed", "en"),
    ("There are many things that we would throw away if we were not "
     "afraid that others might pick them up.", "Oscar Wilde",
     "The Picture of Dorian Gray", "en"),
    ("Experience is simply the name we give our mistakes.",
     "Oscar Wilde", "attributed", "en"),
    ("Whenever people agree with me I always feel I must be wrong.",
     "Oscar Wilde", "attributed", "en"),
    ("The suspense is terrible. I hope it will last.",
     "Oscar Wilde", "The Importance of Being Earnest", "en"),
    ("We are each our own devil, and we make this world our hell.",
     "Oscar Wilde", "The Picture of Dorian Gray", "en"),
    ("The public is wonderfully tolerant. It forgives everything "
     "except genius.", "Oscar Wilde", "attributed", "en"),
    ("Children begin by loving their parents; as they grow older they "
     "judge them; sometimes they forgive them.", "Oscar Wilde",
     "The Picture of Dorian Gray", "en"),
    ("Always forgive your enemies; nothing annoys them so much.",
     "Oscar Wilde", "attributed", "en"),
    ("Some things are more precious because they don't last long.",
     "Oscar Wilde", "The Picture of Dorian Gray", "en"),
]
