<template>
  <v-col
    sm="12"
  >
    <v-card>
      <v-container>
        <v-row align="center" class="px-4">
          <v-col cols="2">
            {{ title }}
          </v-col>
          <v-col cols="8">
            {{ description }}
          </v-col>
          <v-col cols="2">
            <slot v-if="!connected" />
            <v-btn
              v-else
              :loading="removing"
              @click="removeIntegration(integration)"
              color="dark"
              style="color: white"
            >
              {{ $t('buttons.remove') }}
            </v-btn>
          </v-col>
        </v-row>
      </v-container>
    </v-card>
  </v-col>
</template>

<script>
export default {
  name: 'IntegrationItem',
  props: {
    title: {
      type: String,
      default: ''
    },
    description: {
      type: String,
      default: ''
    },
    connected: {
      type: Boolean,
      default: false
    },
    integration: {
      type: Number,
      default: 0
    }
  },
  data: () => ({
    removing: false
  }),
  methods: {
    removeIntegration (integrationId) {
      this.removing = true
      this.$integrations.removeIntegration(integrationId).then((t) => {
        this.$org.getDetailOrgInfo().then((org) => {
          this.$store.commit('setOrg', org)
          this.removing = false
        })
      })
    }
  }
}
</script>
