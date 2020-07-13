<template>
  <v-row>
    <v-col xs="12" mb="8" offset-mb="2" sm="10" offset-sm="1">
      <div>
        <v-row mb-4>
          <v-col sm="6">
            <slot name="header" />
          </v-col>
          <v-col sm="6" style="text-align:right; padding-top:18px; margin-top: 12px;">
            <slot name="header-right" />
          </v-col>
        </v-row>
        <v-container grid-list-md pa-0>
          <v-card>
            <v-row>
              <v-col xs="12">
                <slot name="formpart" />
              </v-col>
            </v-row>
            <v-row class="ma-0">
              <v-col xs="12">
                <slot name="footer" />
              </v-col>
            </v-row>
          </v-card>
        </v-container>
      </div>
    </v-col>
  </v-row>
</template>

<script>
export default {
  layout: 'admin'
}
</script>
