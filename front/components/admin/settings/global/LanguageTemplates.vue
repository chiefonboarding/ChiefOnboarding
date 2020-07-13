<template>
  <div>
    <v-row mb-4>
      <v-col sm="12">
        <h1 class="heading" style="margin-top: 5px;">
          {{ $t('settings.languageSettings') }}
        </h1>
      </v-col>
    </v-row>
    <v-card class="mb-4">
      <v-card-text v-if="loading">
        <LoadingIcon :is-loading="loading" />
      </v-card-text>
      <v-card-text v-else>
        <v-select
          :value="$store.state.selectedLanguage"
          :items="$store.state.languages"
          :label="$t('settings.global.selectLanguage')"
          @change="updateSelectedLanguage"
          item-value="id"
          item-text="language"
          return-object
        />
        <div class="mt-2">
          <v-btn @click="preboardingModal=true">
            {{ $t('settings.global.changePreBoardingEmail') }}
          </v-btn>
          <ChangePreBoardingModal v-if="preboardingModal" v-model="preboardingModal" @emailUpdated="emailUpdated" />
        </div>
        <div class="mt-2">
          <v-btn @click="newHireModal=true">
            {{ $t('settings.global.changeNewHireEmail') }}
          </v-btn>
          <ChangeNewHireModal v-if="newHireModal" v-model="newHireModal" @emailUpdated="emailUpdated" />
        </div>
        <div class="mt-2">
          <v-btn @click="textModal=true">
            {{ $t('settings.global.changeTextMessage') }}
          </v-btn>
          <ChangeTextModal v-if="textModal" v-model="textModal" @emailUpdated="emailUpdated" />
        </div>
        <div class="mt-2">
          <v-btn @click="slackWelcomeModal=true">
            {{ $t('settings.global.changeSlackWelcomeMessage') }}
          </v-btn>
          <ChangeSlackWelcomeMessage v-if="slackWelcomeModal" v-model="slackWelcomeModal" @emailUpdated="emailUpdated" />
        </div>
        <div class="mt-2">
          <v-btn @click="slackKnowledgeModal=true">
            {{ $t('settings.global.changeSlackKnowledgeMessage') }}
          </v-btn>
          <ChangeKnowledgeWelcomeMessage v-if="slackKnowledgeModal" v-model="slackKnowledgeModal" @emailUpdated="emailUpdated" />
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import ChangePreBoardingModal from '@/components/admin/settings/global/language/ChangePreBoardingModal'
import ChangeNewHireModal from '@/components/admin/settings/global/language/ChangeNewHireModal'
import ChangeTextModal from '@/components/admin/settings/global/language/ChangeTextModal'
import ChangeSlackWelcomeMessage from '@/components/admin/settings/global/language/ChangeSlackWelcomeMessage'
import ChangeKnowledgeWelcomeMessage from '@/components/admin/settings/global/language/ChangeKnowledgeWelcomeMessage'
export default {
  name: 'LanguageOptions',
  components: {
    ChangePreBoardingModal,
    ChangeNewHireModal,
    ChangeTextModal,
    ChangeSlackWelcomeMessage,
    ChangeKnowledgeWelcomeMessage
  },
  data: () => ({
    loading: true,
    preboardingModal: false,
    newHireModal: false,
    textModal: false,
    slackWelcomeModal: false,
    slackKnowledgeModal: false
  }),
  mounted () {
    this.$org.getEmails().then((other) => {
      this.loading = false
    })
  },
  methods: {
    updateSelectedLanguage (language) {
      this.$store.commit('updateSelectedLanguage', language)
    },
    emailUpdated () {
      this.loading = true
      this.$org.getEmails().then((other) => {
        this.loading = false
      })
    }
  }
}
</script>
