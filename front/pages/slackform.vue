<template>
  <div>
    <LoadingIcon :is-loading="loading" v-if="loading" />
    <div v-else>
      <v-toolbar
        color="org.base_color"
        dark
        extended
        flat
      />

      <v-card
        class="mx-auto mb-4"
        max-width="590"
        style="margin-top: -64px;"
      >
        <v-card-title>
          <h2>
            {{ Mustaching(toDoUserItem.to_do.name) }}
          </h2>
        </v-card-title>
        <v-card-text v-if="!toDoUserItem.completed_form">
          <ContentDisplay :content="toDoUserItem.to_do.content" />
          <CustomForm
            v-model="toDoUserItem.to_do.form"
            :org="org"
            @input="form = arguments[0]"
          />
          <v-btn
            :color="org.base_color"
            :loading="submittingForm"
            @click="sendFormBack"
            style="margin-left: 0px"
            dark
          >
            {{ $t('buttons.submit') }}
          </v-btn>
        </v-card-text>
        <v-card-text v-else>
          You have already filled in this form!
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script>
import Mustache from 'mustache'
import ContentDisplay from '@/components/portal/ContentDisplay'
import CustomForm from '@/components/preboarding/CustomForm'

export default {
  name: 'Slackform',
  layout: 'empty',
  components: { ContentDisplay, CustomForm },
  data: () => ({
    loading: true,
    toDoUserItem: { to_do: {}, form: [] },
    newHire: {},
    org: {},
    sendingForm: false
  }),
  mounted () {
    this.$user.getCSRFToken().then(() => {
      this.$newhirepreboarding.authenticate(this.$route.query.token).then(() => {
        this.$newhirepart.getSlackToDoItem(this.$route.query.id).then((data) => {
          this.toDoUserItem = data
          this.loading = false
        })
        this.$newhirepart.getMe().then((data) => {
          this.$i18n.locale = data.new_hire.language
          this.$store.commit('setBaseInfo', data)
          this.newHire = data.new_hire
          this.org = data.org
        }).catch(() => {
          this.$store.dispatch('showSnackbar', this.$t('newHirePortal.notAuthorized'))
        })
      }).catch(() => {
        this.$router.push({ name: 'index' })
      })
    })
  },
  methods: {
    Mustaching (content) {
      return Mustache.render(content, this.newHire)
    },
    sendFormBack () {
      this.submittingForm = true
      this.$newhirepart.submitSlackToDoForm(this.toDoUserItem.id, this.toDoUserItem.to_do.form).then((data) => {
        this.toDoUserItem.completed_form = true
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('newHirePortal.genericError'))
      }).finally(() => {
        this.submittingForm = false
      })
    }
  }
}
</script>
