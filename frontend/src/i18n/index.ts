import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

import en from "./locales/en/translation.json";
import es from "./locales/es/translation.json";
import ja from "./locales/ja/translation.json";

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      es: { translation: es },
      ja: { translation: ja },
    },
    fallbackLng: "en",
    interpolation: {
      escapeValue: false,
    },
  });

// Sincronizar el atributo lang del HTML con el idioma activo.
// Esto evita que Chrome auto-traduzca la pagina.
function syncHtmlLang(lng: string) {
  document.documentElement.lang = lng;
}
syncHtmlLang(i18n.language);
i18n.on("languageChanged", syncHtmlLang);

export default i18n;
