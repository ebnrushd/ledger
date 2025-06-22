<template>
  <div class="transfer-funds-view container mx-auto px-4 py-8 max-w-lg">
    <div class="bg-white p-8 rounded-xl shadow-2xl">
      <h2 class="text-3xl font-semibold text-gray-800 text-center mb-8">Inter-Account Transfer</h2>
      <p class="text-gray-600 text-center mb-6">Securely transfer funds between your accounts.</p>

      <div v-if="isLoadingAccounts" class="text-center py-6">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary mx-auto"></div>
        <p class="mt-2 text-gray-500">Loading your accounts...</p>
      </div>
      <div v-if="accountsError"
           class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded-md" role="alert">
        <p class="font-bold">Error Loading Accounts</p>
        <p>{{ accountsError }}</p>
      </div>

      <form @submit.prevent="handleTransfer" v-if="!isLoadingAccounts && !accountsError && userAccounts.length > 0" class="space-y-6">
        <div>
          <label for="fromAccount" class="block text-sm font-medium text-gray-700 mb-1">From Account:</label>
          <select id="fromAccount" v-model="fromAccountId"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm" required>
            <option value="" disabled>Select source account</option>
            <option v-for="account in userAccounts" :key="account.account_id" :value="account.account_id">
              {{ account.account_number }} - {{ account.account_type.charAt(0).toUpperCase() + account.account_type.slice(1) }} (Bal: {{ account.balance.toFixed(2) }} {{ account.currency }})
            </option>
          </select>
        </div>

        <div>
          <label for="toAccount" class="block text-sm font-medium text-gray-700 mb-1">To Account:</label>
          <select id="toAccount" v-model="toAccountId"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm" required :disabled="!fromAccountId || availableToAccounts.length === 0">
            <option value="" disabled>Select destination account</option>
            <option v-for="account in availableToAccounts" :key="account.account_id" :value="account.account_id">
              {{ account.account_number }} - {{ account.account_type.charAt(0).toUpperCase() + account.account_type.slice(1) }} (Bal: {{ account.balance.toFixed(2) }} {{ account.currency }})
            </option>
          </select>
          <div v-if="fromAccountId && availableToAccounts.length === 0" class="mt-1 text-xs text-gray-500">
              No other accounts available for transfer. You need at least two accounts.
          </div>
        </div>

        <div>
          <label for="amount" class="block text-sm font-medium text-gray-700 mb-1">Amount:</label>
          <input type="number" id="amount" v-model.number="amount"
                 class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
                 placeholder="0.00" step="0.01" min="0.01" required />
        </div>

        <div>
          <label for="description" class="block text-sm font-medium text-gray-700 mb-1">Description (Optional):</label>
          <input type="text" id="description" v-model="description"
                 class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
                 placeholder="e.g., For savings" />
        </div>

        <div v-if="transactionsStore.isTransferring" class="text-center py-3">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <p class="mt-2 text-sm text-gray-500">Processing transfer...</p>
        </div>
        <div v-if="transactionsStore.transferError"
             class="my-3 p-3 bg-red-100 text-red-700 border border-red-400 rounded-md text-sm">
            {{ transactionsStore.transferError }}
        </div>
        <div v-if="transactionsStore.transferSuccessMessage"
             class="my-3 p-3 bg-green-100 text-green-700 border border-green-400 rounded-md text-sm">
            {{ transactionsStore.transferSuccessMessage }}
        </div>

        <div class="flex items-center justify-between pt-2">
            <router-link to="/dashboard"
                         class="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary">
                Cancel
            </router-link>
            <button type="submit"
                    class="px-6 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
                    :disabled="transactionsStore.isTransferring || !canSubmit">
            {{ transactionsStore.isTransferring ? 'Transferring...' : 'Transfer Funds' }}
            </button>
        </div>
      </form>
      <div v-if="!isLoadingAccounts && userAccounts.length < 2 && !accountsError" class="mt-6 text-center text-gray-600">
          <p>You need at least two accounts to perform a transfer.
             <router-link v-if="false" to="/open-account" class="font-medium text-primary hover:underline">Open another account now!</router-link>
          </p>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted, onUnmounted } from 'vue';
import { useAccountsStore } from '@/store/accounts';
import { useTransactionsStore } from '@/store/transactions';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';
import type { Account } from '@/types/account';

export default defineComponent({
  name: 'TransferFundsView',
  setup() {
    const accountsStore = useAccountsStore();
    const transactionsStore = useTransactionsStore();
    const router = useRouter();

    const fromAccountId = ref<string | number>('');
    const toAccountId = ref<string | number>('');
    const amount = ref<number | null>(null);
    const description = ref('');

    const { accounts: userAccounts, isLoading: isLoadingAccounts, error: accountsError } = storeToRefs(accountsStore);

    const availableToAccounts = computed(() => {
      if (!fromAccountId.value) return userAccounts.value.filter(acc => acc.status_name === 'active' || acc.status_name === 'frozen'); // Show active/frozen accounts
      return userAccounts.value.filter(
        acc => acc.account_id !== Number(fromAccountId.value) && (acc.status_name === 'active' || acc.status_name === 'frozen')
      );
    });

    const canSubmit = computed(() => {
        return fromAccountId.value &&
               toAccountId.value &&
               amount.value && amount.value > 0 &&
               Number(fromAccountId.value) !== Number(toAccountId.value);
    });

    const handleTransfer = async () => {
      if (!canSubmit.value) {
        // This client-side error could be more specific based on which condition failed.
        transactionsStore.transferError = "Please ensure all fields are correctly filled and source/destination accounts are different.";
        return;
      }

      const transferData = {
        from_account_id: Number(fromAccountId.value),
        to_account_id: Number(toAccountId.value),
        amount: amount.value!,
        description: description.value || undefined,
      };

      const success = await transactionsStore.performTransfer(transferData);

      if (success) {
        fromAccountId.value = '';
        toAccountId.value = '';
        amount.value = null;
        description.value = '';
        setTimeout(() => {
            transactionsStore.clearTransferStatus();
            // router.push('/dashboard'); // Optional: redirect on success
        }, 3000);
      }
    };

    onMounted(() => {
      if (accountsStore.accounts.length === 0) {
        accountsStore.fetchAccounts();
      }
      transactionsStore.clearTransferStatus();
    });

    onUnmounted(() => {
      transactionsStore.clearTransferStatus();
    });

    return {
      fromAccountId, toAccountId, amount, description,
      userAccounts, availableToAccounts,
      isLoadingAccounts, accountsError,
      transactionsStore, // Provide store directly for isTransferring, transferError, transferSuccessMessage
      handleTransfer, canSubmit,
    };
  },
});
</script>

<style scoped>
/* Using Tailwind classes directly in template. Scoped styles for very specific overrides or complex elements. */
/* Example: ensure selects have a min-width if Tailwind's default is too narrow on small screens */
select {
  min-width: 150px; /* Or use Tailwind's w- classes */
}
</style>
```
