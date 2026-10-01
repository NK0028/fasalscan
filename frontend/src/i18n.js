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
  },
};

export function t(lang) {
  return STRINGS[lang] || STRINGS.en;
}

export const RTL_LANGS = new Set(["ur", "ps"]);
