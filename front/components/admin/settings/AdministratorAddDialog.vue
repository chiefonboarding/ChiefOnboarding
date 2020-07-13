<template>
  <v-dialog
    v-model="dialog"
    width="500"
  >
    <template v-slot:activator="{ on }">
      <v-btn
        v-on="on"
        class="success"
        style="margin-right: 0px"
      >
        {{ $t('buttons.add') }}
      </v-btn>
    </template>
    <v-card>
      <v-card-title class="headline">
        {{ $t('settings.addAnAdmin') }}
      </v-card-title>
      <v-card-text>
        <v-form class="mt-3">
          <v-container>
            <v-row>
              <v-flex cols="6">
                <v-text-field
                  v-model="newAdmin.first_name"
                  :label="$t('forms.firstName')"
                  required
                  class="py-0 pr-1"
                />
              </v-flex>
              <v-flex cols="6">
                <v-text-field
                  v-model="newAdmin.last_name"
                  :label="$t('forms.lastName')"
                  required
                  class="py-0 pl-1"
                />
              </v-flex>
            </v-row>
            <v-row>
              <v-text-field
                v-model="newAdmin.email"
                :label="$t('forms.email')"
                class="mt-2 py-0 mb-0"
                required
              />
            </v-row>
          </v-container>

          <v-radio-group v-model="newAdmin.role" label="Pick the scope of their rights:" color="primary">
            <v-radio
              :label="$t('settings.thisPersonHasFull')"
              :value="1"
              color="primary"
            />
            <v-radio
              :label="$t('settings.thisPersonHasOnly')"
              :value="2"
              color="primary"
            />
          </v-radio-group>
        </v-form>
      </v-card-text>
      <v-divider />
      <v-card-actions>
        <v-spacer />
        <v-btn
          @click="dialog=false"
          color="dark"
          text
        >
          {{ $t('buttons.cancel') }}
        </v-btn>
        <v-btn
          :loading="loading"
          @click="add()"
          color="primary"
        >
          {{ $t('buttons.add') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
export default {
  name: 'AdminDialog',
  props: {
    id: {
      type: Number,
      required: true
    }
  },
  data: () => ({
    valid: true,
    dialog: false,
    loading: false,
    isAdmin: false,
    newAdmin: {
      first_name: '',
      last_name: '',
      email: '',
      role: 1
    }
  }),
  watch: {
    dialog () {
      this.newAdmin = {
        first_name: '',
        last_name: '',
        email: '',
        role: 1
      }
    }
  },
  methods: {
    add () {
      this.loading = true
      this.$org.addAdmin(this.newAdmin).then((data) => {
        this.$store.dispatch('showSnackbar', this.$t('settings.adminHasBeenAdded'))
        this.email = ''
        this.name = ''
        this.$org.getAdmins().then((admins) => {
          this.loading = false
        })
        this.dialog = false
      })
    }
  }
}
</script>
