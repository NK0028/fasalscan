// UI strings for the result card and a few shared labels.
// Summaries themselves come translated from the backend.
const STRINGS = {
  en: {
    grade: { A: "Premium", B: "Good", C: "Fair", D: "Process only", "-": "No fruit found" },
    action: {
      hold: "Can hold for a better rate",
      sell_soon: "Sell within a few days",
      sell_now: "Sell today or tomorrow",
      sort_first: "Sort out rotten fruit first",
      process: "Send to processing",
      none: "No fruit detected",
    },
    samples: (n, photos) => `samples checked${photos > 1 ? ` in ${photos} photos` : ""}`,
    damaged: "damaged",
    daysLeft: "days left",
    fresh: "fresh",
    rotten: "rotten",
    byFruit: "By fruit",
    shelfRange: "Shelf-life range",
    days: "days (estimate)",
    weather: "Weather used",
    weatherLive: (w) => `${Math.round(w.temp_c)}°C now · ${Math.round(w.outlook_c)}°C avg next days · ${Math.round(w.humidity)}% humidity`,
    weatherSeasonal: (w) => `${Math.round(w.outlook_c)}°C seasonal average for Swat`,
    scanAnother: "Scan another crate",

    // App shell
    tabs: { scan: "Scan", history: "History", ask: "Ask" },
    logout: "Log out",
    langSelect: "Language",
    footer: "Estimates only. Built with YOLOv8, Whisper and open-weight LLMs. MVP by Naeem Khan.",

    // Fruit names: plural for captions, "of" form for "N orange samples"
    fruitPlural: { apple: "apples", banana: "bananas", orange: "oranges" },
    fruitAttr: { apple: "apple", banana: "banana", orange: "orange", unknown: "fruit" },
    items: "items",

    // Scan
    hello: (name) => `Salam, ${name}. Pick a few fruit from the crate and snap each one close up, in daylight.`,
    dzTitle: "Photograph your fruit",
    dzSub: "Apples, bananas and oranges in this version",
    takePhoto: "Take photo",
    choosePhotos: "Choose photos",
    fromGallery: "From gallery",
    tip: "Tip: pick 4-8 fruit at random from the crate and photograph each one close up. More photos, fairer grade.",
    sampleHint: "No fruit nearby? Try a sample lot:",
    lots: { apple: "Apples", orange: "Oranges", banana: "Bananas" },
    photos: (n) => `${n} photo${n === 1 ? "" : "s"}`,
    maxPhotos: (n) => `max ${n}`,
    clearAll: "Clear all",
    scanPhotos: (n) => `Scan ${n} photo${n === 1 ? "" : "s"}`,
    scanning: "Scanning…",
    adding: "Adding…",
    useLocation: "Use my location for weather (default: Swat)",
    checking: (n) => `Checking ${n} photo${n === 1 ? "" : "s"}…`,
    nothingFound: "Nothing found",
    photoAlt: (i) => `Photo ${i}`,
    removePhoto: (i) => `Remove photo ${i}`,
    errNotImages: "Some files weren't images and were skipped.",
    errTooMany: (n) => `Up to ${n} photos per scan, extra ones were skipped.`,
    errSample: "Couldn't load that sample.",
    errNetwork: "Couldn't reach the server. It may still be waking up, try again in a few seconds.",

    // History
    histLoading: "Loading your scans…",
    histEmpty: "No scans yet. Your scanned crates will show up here.",
    damagedPct: (p) => `${p}% damaged`,
    daysApprox: (n) => `~${n} days`,

    // Ask
    askAbout: (n, fruit, grade) => `Asking about your latest scan: ${n} ${fruit} samples, grade ${grade}.`,
    askNoScan: "Scan a crate first for answers about your own fruit, or ask a general question.",
    askPlaceholder: "Ask anything about your fruit…",
    send: "Send",
    offline: "offline answer",
    micStart: "Speak your question",
    micStop: "Stop recording",
    errTooShort: "That was too short, hold the button and speak.",
    errMic: "Microphone permission was denied.",
  },
  ur: {
    grade: { A: "اعلیٰ", B: "اچھا", C: "درمیانہ", D: "صرف پروسیسنگ", "-": "کوئی پھل نہیں ملا" },
    action: {
      hold: "بہتر ریٹ کا انتظار کر سکتے ہیں",
      sell_soon: "چند دنوں میں بیچ دیں",
      sell_now: "آج یا کل بیچ دیں",
      sort_first: "پہلے خراب پھل الگ کریں",
      process: "پروسیسنگ کے لیے بھیجیں",
      none: "کوئی پھل نہیں ملا",
    },
    samples: (n, photos) => `نمونے جانچے گئے${photos > 1 ? ` (${photos} تصاویر)` : ""}`,
    damaged: "خراب",
    daysLeft: "دن باقی",
    fresh: "تازہ",
    rotten: "خراب",
    byFruit: "پھل کے لحاظ سے",
    shelfRange: "اندازاً مدت",
    days: "دن (اندازہ)",
    weather: "موسم",
    weatherLive: (w) => `ابھی ${Math.round(w.temp_c)}°C · اگلے دنوں کا اوسط ${Math.round(w.outlook_c)}°C · نمی ${Math.round(w.humidity)}٪`,
    weatherSeasonal: (w) => `سوات کا موسمی اوسط ${Math.round(w.outlook_c)}°C`,
    scanAnother: "اگلا کریٹ سکین کریں",

    tabs: { scan: "سکین", history: "پچھلے سکین", ask: "پوچھیں" },
    logout: "باہر نکلیں",
    langSelect: "زبان",
    footer: "یہ صرف اندازے ہیں۔ YOLOv8\u200F، Whisper اور اوپن ویٹ لسانی ماڈلز (LLMs) سے بنایا گیا۔ ابتدائی نمونہ (MVP): Naeem Khan۔",

    fruitPlural: { apple: "سیب", banana: "کیلے", orange: "مالٹے" },
    fruitAttr: { apple: "سیبوں", banana: "کیلوں", orange: "مالٹوں", unknown: "پھلوں" },
    items: "دانے",

    hello: (name) => `السلام علیکم، ${name}۔ کریٹ میں سے چند پھل نکالیں اور دن کی روشنی میں ہر ایک کی قریب سے تصویر لیں۔`,
    dzTitle: "اپنے پھل کی تصویر لیں",
    dzSub: "اس ورژن میں سیب، کیلے اور مالٹے",
    takePhoto: "تصویر لیں",
    choosePhotos: "تصویریں چنیں",
    fromGallery: "گیلری سے",
    tip: "مشورہ: کریٹ میں مختلف جگہوں سے 4 سے 8 پھل اٹھائیں اور ہر ایک کی قریب سے تصویر لیں۔ جتنی زیادہ تصویریں، اتنا ہی درست گریڈ۔",
    sampleHint: "پاس پھل نہیں ہے؟ کوئی نمونہ آزمائیں:",
    lots: { apple: "سیب", orange: "مالٹے", banana: "کیلے" },
    photos: (n) => (n === 1 ? "1 تصویر" : `${n} تصویریں`),
    maxPhotos: (n) => `زیادہ سے زیادہ ${n}`,
    clearAll: "سب ہٹائیں",
    scanPhotos: (n) => (n === 1 ? "1 تصویر سکین کریں" : `${n} تصویریں سکین کریں`),
    scanning: "سکین ہو رہا ہے…",
    adding: "شامل ہو رہی ہیں…",
    useLocation: "موسم کے لیے میرا مقام استعمال کریں (ورنہ سوات)",
    checking: (n) => (n === 1 ? "1 تصویر جانچی جا رہی ہے…" : `${n} تصویریں جانچی جا رہی ہیں…`),
    nothingFound: "کچھ نہیں ملا",
    photoAlt: (i) => `تصویر ${i}`,
    removePhoto: (i) => `تصویر ${i} ہٹائیں`,
    errNotImages: "کچھ فائلیں تصویریں نہیں تھیں، انہیں چھوڑ دیا گیا۔",
    errTooMany: (n) => `ایک سکین میں زیادہ سے زیادہ ${n} تصویریں، باقی چھوڑ دی گئیں۔`,
    errSample: "یہ نمونہ کھل نہیں سکا۔",
    errNetwork: "سرور سے رابطہ نہیں ہو سکا۔ شاید ابھی چالو ہو رہا ہے، چند سیکنڈ بعد دوبارہ کوشش کریں۔",

    histLoading: "آپ کے سکین کھل رہے ہیں…",
    histEmpty: "ابھی کوئی سکین نہیں۔ آپ کے سکین کیے ہوئے کریٹ یہاں نظر آئیں گے۔",
    damagedPct: (p) => `${p}% خراب`,
    daysApprox: (n) => `تقریباً ${n} دن`,

    askAbout: (n, fruit, grade) => `آپ کے پچھلے سکین کے بارے میں: ${fruit} کے ${n} نمونے، گریڈ ${grade}۔`,
    askNoScan: "اپنے پھل کے بارے میں جواب کے لیے پہلے کریٹ سکین کریں، یا کوئی عام سوال پوچھیں۔",
    askPlaceholder: "اپنا سوال لکھیں…",
    send: "بھیجیں",
    offline: "آف لائن جواب",
    micStart: "اپنا سوال بول کر پوچھیں",
    micStop: "ریکارڈنگ روکیں",
    errTooShort: "آواز بہت مختصر تھی، بٹن دبائیں اور بولیں۔",
    errMic: "مائیک کی اجازت نہیں ملی۔",
  },
  ps: {
    grade: { A: "ډېر ښه", B: "ښه", C: "منځنی", D: "یوازې پروسس", "-": "مېوه ونه موندل شوه" },
    action: {
      hold: "د ښه نرخ انتظار کولی شئ",
      sell_soon: "په څو ورځو کې یې وپلورئ",
      sell_now: "نن یا سبا یې وپلورئ",
      sort_first: "لومړی خرابې مېوې جلا کړئ",
      process: "پروسس ته یې ولېږئ",
      none: "مېوه ونه موندل شوه",
    },
    samples: (n, photos) => `نمونې وکتل شوې${photos > 1 ? ` (${photos} انځورونه)` : ""}`,
    damaged: "خراب",
    daysLeft: "ورځې پاتې",
    fresh: "تازه",
    rotten: "خراب",
    byFruit: "د مېوې له مخې",
    shelfRange: "اټکلي موده",
    days: "ورځې (اټکل)",
    weather: "هوا",
    weatherLive: (w) => `اوس ${Math.round(w.temp_c)}°C · د راتلونکو ورځو منځنۍ ${Math.round(w.outlook_c)}°C · لندبل ${Math.round(w.humidity)}٪`,
    weatherSeasonal: (w) => `د سوات موسمي منځنۍ ${Math.round(w.outlook_c)}°C`,
    scanAnother: "بل کریټ سکین کړئ",

    tabs: { scan: "سکین", history: "تاریخچه", ask: "پوښتنه" },
    logout: "ووځئ",
    langSelect: "ژبه",
    footer: "دا یوازې اټکلونه دي. د YOLOv8\u200F، Whisper او اوپن ویټ ژبني ماډلونو (LLMs) په مرسته جوړ شوی. لومړنۍ بېلګه (MVP): Naeem Khan.",

    fruitPlural: { apple: "مڼې", banana: "کېلې", orange: "مالټې" },
    fruitAttr: { apple: "مڼو", banana: "کېلو", orange: "مالټو", unknown: "مېوو" },
    items: "دانې",

    hello: (name) => `سلام، ${name}. له کریټ نه څو مېوې راواخلئ او د ورځې په رڼا کې د هرې یوې له نږدې انځور واخلئ.`,
    dzTitle: "د خپلې مېوې انځور واخلئ",
    dzSub: "په دې نسخه کې مڼې، کېلې او مالټې",
    takePhoto: "انځور واخلئ",
    choosePhotos: "انځورونه وټاکئ",
    fromGallery: "له ګالرۍ",
    tip: "مشوره: د کریټ له بېلابېلو ځایونو 4 تر 8 مېوې راواخلئ او د هرې یوې له نږدې انځور واخلئ. څومره ډېر انځورونه، هومره سمه درجه.",
    sampleHint: "مېوه مو نږدې نشته؟ یوه نمونه وازمویئ:",
    lots: { apple: "مڼې", orange: "مالټې", banana: "کېلې" },
    photos: (n) => (n === 1 ? "1 انځور" : `${n} انځورونه`),
    maxPhotos: (n) => `تر ${n} پورې`,
    clearAll: "ټول لرې کړئ",
    scanPhotos: (n) => (n === 1 ? "1 انځور سکین کړئ" : `${n} انځورونه سکین کړئ`),
    scanning: "سکین کېږي…",
    adding: "ورزیاتېږي…",
    useLocation: "د هوا لپاره زما ځای وکاروئ (که نه، سوات)",
    checking: (n) => (n === 1 ? "1 انځور کتل کېږي…" : `${n} انځورونه کتل کېږي…`),
    nothingFound: "هېڅ ونه موندل شول",
    photoAlt: (i) => `انځور ${i}`,
    removePhoto: (i) => `انځور ${i} لرې کړئ`,
    errNotImages: "ځینې فایلونه انځورونه نه وو، پرېښودل شول.",
    errTooMany: (n) => `په یوه سکین کې تر ${n} انځورونو پورې، نور پرېښودل شول.`,
    errSample: "دا نمونه پرانیستل نه شوه.",
    errNetwork: "سرور ته ونه رسېدو. کېدای شي لا چالانېږي، څو ثانیې وروسته بیا هڅه وکړئ.",

    histLoading: "ستاسو سکینونه راځي…",
    histEmpty: "تر اوسه هېڅ سکین نشته. ستاسو سکین شوي کریټونه به دلته ښکاري.",
    damagedPct: (p) => `${p}% خراب`,
    daysApprox: (n) => `نږدې ${n} ورځې`,

    askAbout: (n, fruit, grade) => `ستاسو د وروستي سکین په اړه: د ${fruit} ${n} نمونې، درجه ${grade}.`,
    askNoScan: "د خپلې مېوې په اړه د ځواب لپاره لومړی یو کریټ سکین کړئ، یا کومه عامه پوښتنه وکړئ.",
    askPlaceholder: "خپله پوښتنه ولیکئ…",
    send: "ولېږئ",
    offline: "آفلاین ځواب",
    micStart: "خپله پوښتنه په غږ وکړئ",
    micStop: "ثبت ودروئ",
    errTooShort: "غږ ډېر لنډ و، تڼۍ کېکاږئ او وغږېږئ.",
    errMic: "د مایک اجازه ورنه کړل شوه.",
  },
};

export function t(lang) {
  return STRINGS[lang] || STRINGS.en;
}

export const RTL_LANGS = new Set(["ur", "ps"]);

// Fruit name in the given form ("fruitPlural" | "fruitAttr"); unknown fruit falls back to the raw key.
export function fruitName(lang, fruit, form = "fruitPlural") {
  const s = t(lang);
  if (!fruit || fruit === "unknown") return form === "fruitAttr" ? s.fruitAttr.unknown : s.items;
  return s[form]?.[fruit] || STRINGS.en[form]?.[fruit] || fruit;
}

// Translate network errors from api.js; server messages are shown as sent.
export function errorText(lang, err) {
  if (err && err.status === 0) return t(lang).errNetwork;
  return err?.message || String(err);
}
