import Vue from 'vue'
import VueI18n from 'vue-i18n'
import en from '~/locale/en.json'
import nl from '~/locale/nl.json'
import es from '~/locale/es.json'
import fr from '~/locale/fr.json'
import jp from '~/locale/jp.json'
import pt from '~/locale/pt.json'
import de from '~/locale/de.json'
import tr from '~/locale/tr.json'

Vue.use(VueI18n)

export default ({ app, store }) => {
  app.i18n = new VueI18n({
    locale: 'en',
    fallbackLocale: 'en',
    messages: {
      en,
      nl,
      es,
      jp,
      fr,
      pt,
      tr,
      de
    }
  })
}
