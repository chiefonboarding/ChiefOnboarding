<template>
  <v-container grid-list-xl px-6 py-1 fluid>
    <LoadingIcon :is-loading="loading" />
    <v-row v-if="!loading" row wrap>
      <v-col
        v-if="$store.state.org.slack_account_key && $store.state.org.slack_key"
        sm="6"
      >
        <div class="border">
          <div>
            <h3>Slack</h3>
            <p>{{ $t("newhires.slackExpl") }}</p>
            <v-btn v-if="slack.status === 'not_found'" @click="addSlackModal = true" color="secondary" class="ma-0">
              {{ $t("newhires.giveAccess") }}
            </v-btn>
            <v-menu v-else offset-y>
              <template v-slot:activator="{ on }">
                <v-btn
                  :class="{'primary': slack.status === 'pending', 'green': slack.status === 'exists'}"
                  :loading="loadingSlack"
                  v-on="on"
                  class="ma-0"
                >
                  <span v-if="slack.status === 'pending'">{{ $t("buttons.pending") }}</span><span v-else style="color:white">{{ $t("buttons.active") }}</span>
                </v-btn>
              </template>
              <v-list>
                <v-list-item
                  @click="removeSlack"
                >
                  <v-list-item-title>{{ $t("buttons.remove") }}</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>
          </div>
        </div>
      </v-col>
      <v-col
        v-if="$store.state.org.google_key"
        sm="6"
      >
        <div class="border">
          <div>
            <h3>Google</h3>
            <p>{{ $t("newhires.googleExpl") }}</p>
            <v-btn v-if="google.status === 'not_found'" @click="addGoogleModal = true" color="secondary" class="ma-0">
              {{ $t("newhires.giveAccess") }}
            </v-btn>
            <v-menu v-else offset-y>
              <template v-slot:activator="{ on }">
                <v-btn
                  :class="{'primary': google.status === 'pending', 'green': google.status === 'exists'}"
                  :loading="loadingGoogle"
                  v-on="on"
                  class="ma-0"
                >
                  <span v-if="google.status === 'pending'">{{ $t("buttons.pending") }}</span><span v-else style="color:white">{{ $t("buttons.active") }}</span>
                </v-btn>
              </template>
              <v-list>
                <v-list-item
                  @click="removeGoogle"
                >
                  <v-list-item-title>{{ $t("buttons.remove") }}</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>
          </div>
        </div>
      </v-col>
      <v-col
        v-if="$store.state.org.asana"
        sm="6"
      >
        <div class="border">
          <div>
            <h3>Asana</h3>
            <p>Asana account creation</p>
            <v-btn v-if="asana.status === 'not_found'" @click="addGoogleModal = true" color="secondary" class="ma-0">
              {{ $t("newhires.giveAccess") }}
            </v-btn>
            <v-menu v-else offset-y>
              <template v-slot:activator="{ on }">
                <v-btn
                  :class="{'primary': asana.status === 'pending', 'green': asana.status === 'exists'}"
                  :loading="loadingGoogle"
                  v-on="on"
                  class="ma-0"
                >
                  <span v-if="asana.status === 'pending'">{{ $t("buttons.pending") }}</span><span v-else style="color:white">{{ $t("buttons.active") }}</span>
                </v-btn>
              </template>
              <v-list>
                <v-list-item
                  @click="removeGoogle"
                >
                  <v-list-item-title>{{ $t("buttons.remove") }}</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>
          </div>
        </div>
      </v-col>
    </v-row>
    <v-dialog v-model="addSlackModal" max-width="500">
      <v-card>
        <v-card-title><h3>{{ $t("newhires.slackWhere") }}</h3></v-card-title>
        <v-card-text>
          {{ $t("newhires.slackDefault") }}

          <v-text-field
            v-model="slackEmail"
            :label="$t('forms.email')"
            class="mt-4"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="addSlackModal = false" color="secondary">
            {{ $t("buttons.cancel") }}
          </v-btn>
          <v-btn :loading="schedulingSlack" @click="createSlack" color="primary">
            {{ $t("buttons.schedule") }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-dialog v-model="addGoogleModal" max-width="500">
      <v-card>
        <v-card-title><h3>{{ $t("newhires.modalGoogleTitle") }}</h3></v-card-title>
        <v-card-text>
          <p v-html="$t('newhires.modalGoogleDescr')" />
          <v-text-field
            v-model="googleEmail"
            :label="$t('forms.email')"
            class="mt-4"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="addGoogleModal = false" color="secondary" text>
            {{ $t("buttons.cancel") }}
          </v-btn>
          <v-btn @click="createGoogle" color="primary">
            {{ $t("buttons.schedule") }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
export default {
  props: {
    newHire: {
      type: Object,
      required: true
    }
  },
  data: () => ({
    loading: false,
    slack: {},
    google: {},
    asana: {},
    googleEmail: '',
    addSlackModal: false,
    slackEmail: '',
    schedulingSlack: false,
    schedulingGoogle: false,
    loadingSlack: true,
    loadingGoogle: true,
    creatingSlack: false,
    creatingGoogle: false,
    addGoogleModal: false
  }),
  mounted () {
    this.checkAccounts()
  },
  methods: {
    createSlack () {
      this.schedulingSlack = true
      this.$newhires.scheduleAccess(this.newHire.id, { integration: 1, email: this.slackEmail }).then((data) => {
        this.slack.status = 'pending'
        this.slackEmail = ''
        this.addSlackModal = false
      }).catch((error) => {

      }).finally(() => {
        this.schedulingSlack = false
      })
    },
    removeSlack () {
      this.loadingSlack = true
      this.$newhires.revokeAccess(this.newHire.id, { integration: 1 }).then((data) => {
        this.slack.status = 'not_found'
      }).catch((error) => {
        if (error.error === 'paid') {
          this.$store.dispatch('showSnackbar', 'This feature is only available for paying Slack teams.')
        }
        if (error.error === 'error') {
          this.$store.dispatch('showSnackbar', 'Something went wrong, please try again.')
        }
      }).finally(() => {
        this.loadingSlack = false
      })
    },
    createGoogle () {
      this.creatingGoogle = true
      this.$newhires.scheduleAccess(this.newHire.id, { integration: 2, email: this.googleEmail }).then((data) => {
        this.google.status = 'pending'
        this.googleEmail = ''
        this.addGoogleModal = false
      }).finally(() => {
        this.creatingGoogle = false
      })
    },
    removeGoogle () {
      this.loadingGoogle = true
      this.$newhires.revokeAccess(this.newHire.id, { integration: 2 }).then((data) => {
        this.google.status = 'not_found'
      }).finally(() => {
        this.loadingGoogle = false
      })
    },
    checkAccounts () {
      if (this.$store.state.org.slack_account_key && this.$store.state.org.slack_key) {
        this.$newhires.getAccess(this.newHire.id, 1).then((data) => {
          this.slack = data
        }).finally(() => {
          this.loadingSlack = false
          this.slackEmail = this.newHire.email
        })
      }
      if (this.$store.state.org.google_key) {
        this.$newhires.getAccess(this.newHire.id, 2).then((data) => {
          this.google = data
        }).finally(() => {
          this.loadingGoogle = false
        })
      }
      if (this.$store.state.org.asana) {
        this.$newhires.getAccess(this.newHire.id, 4).then((data) => {
          this.asana = data
        }).finally(() => {
          this.loadingGoogle = false
        })
      }
    }
  }
}
</script>

<style scoped>
.border {
  border: 1px solid white;
  border-radius: 4px;
  padding: 10px;
}
.pending {
  border: 1px solid #67aaf9;
}
.active {
  border: 1px solid #ffbb42;
}
</style>
