<template>
  <v-row>
    <v-col sm="12" mb="8" offset-mb="2" md="10" offset-sm="1">
      <div>
        <v-row mb-4>
          <v-col sm="6">
            <h1 class="heading" style="margin-top: 10px; margin-left: 11px;">
              {{ newHire.first_name }} {{ newHire.last_name }}
            </h1>
          </v-col>
          <v-col sm="6" style="text-align:right;">
            <v-menu bottom left>
              <template v-slot:activator="{ on }">
                <v-btn
                  v-on="on"
                  icon
                  style="margin-top: 15px;font-size: 20px"
                >
                  <v-icon>settings</v-icon>
                </v-btn>
              </template>

              <v-list>
                <v-list-item
                  @click="preboardingDialog = true; phone = newHire.phone"
                >
                  <v-list-item-title>{{ $t("newhires.sendPreMail") }}</v-list-item-title>
                </v-list-item>
                <v-list-item
                  @click="loginSendForm = true"
                >
                  <v-list-item-title>{{ $t("newhires.sendLoginMail") }}</v-list-item-title>
                </v-list-item>
                <v-list-item
                  @click="addSequence = true"
                >
                  <v-list-item-title>Add sequence</v-list-item-title>
                </v-list-item>
                <v-divider />
                <v-list-item
                  @click="dialog = true"
                >
                  <v-list-item-title>{{ $t("buttons.remove") }}</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>
          </v-col>
        </v-row>
        <v-container grid-list-md pa-0>
          <v-row mb-4>
            <v-col sm="12">
              <v-card class="mb-4 second">
                <v-col style="padding: 0px;">
                  <v-tabs
                    v-model="active"
                    dark
                    slider-color="primary"
                  >
                    <v-tab @click="$router.push({name: 'admin-newhire-id', params: {'id': $route.params.id}})" ripple>
                      {{ $t("newhires.timeline") }}
                    </v-tab>
                    <v-tab @click="$router.push({name: 'admin-newhire-id-profile', params: {'id': $route.params.id}})" ripple>
                      {{ $t("newhires.profile") }}
                    </v-tab>
                    <v-tab
                      @click="$router.push({name: 'admin-newhire-id-access', params: {'id': $route.params.id}})"
                      v-if="$store.state.org.google_key || $store.state.org.slack_account_key"
                      ripple
                    >
                      {{ $t("newhires.access") }}
                    </v-tab>
                    <v-tab @click="$router.push({name: 'admin-newhire-id-tasks', params: {'id': $route.params.id}})" ripple>
                      {{ $t("newhires.tasks") }}
                    </v-tab>
                    <v-tab @click="$router.push({name: 'admin-newhire-id-progress', params: {'id': $route.params.id}})" ripple>
                      {{ $t("newhires.progress") }}
                    </v-tab>
                    <v-tab @click="$router.push({name: 'admin-newhire-id-forms', params: {'id': $route.params.id}})" ripple>
                      {{ $t("newhires.forms") }}
                    </v-tab>
                    <v-tab @click="$router.push({name: 'admin-newhire-id-notes', params: {'id': $route.params.id}})" ripple>
                      {{ $t("newhires.notes") }}
                    </v-tab>
                    <v-tab @click="$router.push({name: 'admin-newhire-id-admintasks', params: {'id': $route.params.id}})" ripple>
                      {{ $t("newhires.adminTasks") }}
                    </v-tab>
                    <v-tab @click="$router.push({name: 'admin-newhire-id-welcome', params: {'id': $route.params.id}})" ripple>
                      {{ $t("newhires.welcomeMessages") }}
                    </v-tab>
                  </v-tabs>
                  <div class="pa3">
                    <nuxt-child />
                  </div>
                </v-col>
              </v-card>
            </v-col>
          </v-row>
        </v-container>
      </div>
    </v-col>
    <v-dialog
      v-model="dialog"
      :persistent="true"
      max-width="650"
    >
      <v-card>
        <v-card-title class="headline">
          {{ $t("newhires.removeNewHireHeader") }}
        </v-card-title>
        <v-card-text>
          <p v-html="$t('newhires.removeNewHireDescr')" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="dialog = false" color="secondary" text>
            {{ $t('buttons.cancel') }}
          </v-btn>
          <v-btn :loading="removing" @click="remove()" color="red" style="color: white">
            {{ $t("buttons.remove") }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-dialog
      v-model="loginSendForm"
      :persistent="true"
      max-width="650"
    >
      <v-card>
        <v-card-title class="headline">
          {{ $t("newhires.sendEmailHeader") }}
        </v-card-title>
        <v-card-text>
          <p v-html="$t('newhires.sendEmailNewHireDescr')" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="loginSendForm = false" color="secondary" text>
            {{ $t('buttons.cancel') }}
          </v-btn>
          <v-btn :loading="sendingEmail" @click="sendLoginEmail()" color="primary" style="color: white">
            {{ $t("buttons.send") }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <SendPreboardingModal v-model="preboardingDialog" :newhire="newHire" @changeNewHire="newHire = arguments[0]" />
    <SelectTemplates v-if="addSequence" v-model="addSequence" :items="this.$store.state.sequences.all" @clickedItem="addSequenceToNewHire" />
    <SequenceItemsNeverTriggeredModal v-model="neverTriggeredModal" :conditions="conditionItems" :new-hire="newHire" />
  </v-row>
</template>

<script>
import SequenceItemsNeverTriggeredModal from '@/components/admin/sequence/modals/SequenceItemsNeverTriggeredModal'
import SendPreboardingModal from '@/components/admin/preboarding/SendPreboardingModal'
export default {
  layout: 'admin',
  components: { SequenceItemsNeverTriggeredModal, SendPreboardingModal },
  data: () => ({
    loading: true,
    submittingForm: false,
    removing: false,
    errors: { details: {} },
    newHire: {},
    dialog: false,
    preboardingDialog: false,
    disabledForm: true,
    refreshForm: true,
    newHireTemp: {},
    active: 0,
    loadingPrev: false,
    sendingEmail: false,
    loginSendForm: false,
    updatingAccount: false,
    addSequence: false,
    neverTriggeredModal: false,
    conditionItems: []
  }),
  mounted () {
    this.getNewHire()
    if (this.$route.name === 'admin-newhire-id') {
      this.active = 0
    } else if (this.$route.name === 'admin-newhire-id-profile') {
      this.active = 1
    } else if (this.$route.name === 'admin-newhire-id-access') {
      this.active = 2
    } else if (this.$route.name === 'admin-newhire-id-tasks') {
      this.active = 3
    } else if (this.$route.name === 'admin-newhire-id-progress') {
      this.active = 4
    } else if (this.$route.name === 'admin-newhire-id-forms') {
      this.active = 5
    } else if (this.$route.name === 'admin-newhire-id-notes') {
      this.active = 6
    } else if (this.$route.name === 'admin-newhire-id-admintasks') {
      this.active = 7
    } else if (this.$route.name === 'admin-newhire-id-welcome') {
      this.active = 8
    }
  },
  methods: {
    getNewHire () {
      this.$newhires.get(this.$route.params.id).then((newHire) => {
        this.newHire = newHire
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('newhires.noNewHire'))
      }).finally(() => {
        this.loading = false
      })
    },
    sendLoginEmail () {
      this.sendingEmail = true
      this.$newhires.sendLoginEmail(this.$route.params.id).then((data) => {
        this.$store.dispatch('showSnackbar', this.$t('newhires.emailHasBeenSend'))
        this.loginSendForm = false
      }).catch((error) => {
      }).finally(() => {
        this.sendingEmail = false
      })
    },
    remove () {
      this.removing = true
      this.$newhires.remove(this.$route.params.id).then((newhire) => {
        this.$newhires.getAll()
        this.dialog = false
        this.$store.dispatch('showSnackbar', this.$t('newhires.removed'))
        this.$router.push({ 'name': 'admin-newhire' })
      }).catch((errors) => {
        this.$store.dispatch('showSnackbar', this.$t('newhires.notRemoved'))
      }).finally(() => {
        this.removing = false
      })
    },
    addSequenceToNewHire (item) {
      this.$newhires.addSequence(this.$route.params.id, item).then(() => {
        this.$newhires.checkPastSequenceItems(this.$route.params.id, [item.id]).then((conditionItems) => {
          if (conditionItems.length) {
            this.neverTriggeredModal = true
            this.conditionItems = conditionItems
          }
          this.$store.commit('toggleRefreshSequence')
        })
        this.addSequence = false
        this.$store.dispatch('showSnackbar', 'Sequence has been added.')
      })
    }
  }
}
</script>

<style scoped>
.border-bottom {
  border-bottom: 1px solid rgb(228, 228, 228);
}
.second {
  margin-left: 10px;
}
.first {
  margin-right: 10px;
}
</style>
