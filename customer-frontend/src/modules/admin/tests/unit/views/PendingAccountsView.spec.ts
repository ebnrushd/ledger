import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { useAdminAccountsStore } from '@admin/store/adminAccounts';
import PendingAccountsView from '@admin/views/PendingAccountsView.vue';
import { nextTick } from 'vue';

// Mock Vue Router
const mockRouter = {
  push: vi.fn(),
};
vi.mock('vue-router', async () => {
  const actual = await vi.importActual('vue-router');
  return {
    ...actual,
    useRouter: () => mockRouter,
    useRoute: () => ({ query: {} }), // Mock route as needed
    RouterLink: { template: '<a><slot /></a>' } // Stub RouterLink
  };
});


describe('PendingAccountsView.vue', () => {
  let pinia;
  let accountsStore;

  beforeEach(() => {
    pinia = createPinia();
    setActivePinia(pinia);
    accountsStore = useAdminAccountsStore();

    // Reset store state and mocks
    accountsStore.accounts = [];
    accountsStore.isLoadingList = false;
    accountsStore.error = null;
    accountsStore.updateError = null;
    accountsStore.successMessage = null;
    accountsStore.currentPage = 1;
    accountsStore.totalPages = 1;
    accountsStore.itemsPerPage = 10;
    accountsStore.isUpdatingStatus = false;

    accountsStore.fetchAccounts = vi.fn();
    accountsStore.updateAccountStatus = vi.fn();
    accountsStore.clearMessages = vi.fn();
  });

  it('calls fetchAccounts with pending_approval filter on mount', () => {
    mount(PendingAccountsView, { global: { plugins: [pinia] } });
    expect(accountsStore.clearMessages).toHaveBeenCalled();
    expect(accountsStore.fetchAccounts).toHaveBeenCalledWith(1, 10, { status_name: 'pending_approval' });
  });

  it('renders loading state correctly', () => {
    accountsStore.isLoadingList = true;
    const wrapper = mount(PendingAccountsView, { global: { plugins: [pinia] } });
    expect(wrapper.text()).toContain('Loading pending accounts...');
    expect(wrapper.find('.animate-spin').exists()).toBe(true);
  });

  it('renders error state correctly', () => {
    accountsStore.error = 'Failed to load';
    const wrapper = mount(PendingAccountsView, { global: { plugins: [pinia] } });
    expect(wrapper.text()).toContain('Error Loading Accounts');
    expect(wrapper.text()).toContain('Failed to load');
  });

  it('renders a list of pending accounts', async () => {
    accountsStore.accounts = [
      { account_id: 1, account_number: 'ACC001', customer_first_name: 'John', customer_last_name: 'Doe', customer_id: 10, account_type: 'savings', balance: 100, currency: 'USD', opened_at: new Date().toISOString(), status_name: 'pending_approval', overdraft_limit:0 },
      { account_id: 2, account_number: 'ACC002', customer_first_name: 'Jane', customer_last_name: 'Smith', customer_id: 11, account_type: 'checking', balance: 200, currency: 'USD', opened_at: new Date().toISOString(), status_name: 'pending_approval', overdraft_limit:0  },
    ] as any; // Cast as any to satisfy stricter AdminAccount type if some fields are missing in mock
    accountsStore.totalPages = 1;

    const wrapper = mount(PendingAccountsView, { global: { plugins: [pinia] } });
    await nextTick(); // Wait for DOM update

    const rows = wrapper.findAll('tbody tr');
    expect(rows.length).toBe(2);
    expect(wrapper.text()).toContain('ACC001');
    expect(wrapper.text()).toContain('John Doe');
    expect(wrapper.text()).toContain('ACC002');
    expect(wrapper.text()).toContain('Jane Smith');
  });

  it('calls approveAccount store action when Approve button is clicked', async () => {
    accountsStore.accounts = [
      { account_id: 1, account_number: 'ACC001', customer_id:1, customer_first_name: 'Test', customer_last_name: 'User', account_type: 'savings', balance: 0, currency: 'USD', opened_at: '2023-01-01T00:00:00.000Z', status_name: 'pending_approval', overdraft_limit:0 }
    ] as any;
    const wrapper = mount(PendingAccountsView, { global: { plugins: [pinia] } });
    await nextTick();

    const approveButton = wrapper.find('tbody tr:first-child button.bg-green-500');
    await approveButton.trigger('click');

    expect(accountsStore.clearMessages).toHaveBeenCalledTimes(2); // Once on mount, once on action
    expect(accountsStore.updateAccountStatus).toHaveBeenCalledWith(1, 'active', expect.any(Function));
  });

  it('calls rejectAccount store action when Reject button is clicked', async () => {
    accountsStore.accounts = [
      { account_id: 1, account_number: 'ACC001', customer_id:1, customer_first_name: 'Test', customer_last_name: 'User', account_type: 'savings', balance: 0, currency: 'USD', opened_at: '2023-01-01T00:00:00.000Z', status_name: 'pending_approval', overdraft_limit:0 }
    ] as any;
    const wrapper = mount(PendingAccountsView, { global: { plugins: [pinia] } });
    await nextTick();

    const rejectButton = wrapper.find('tbody tr:first-child button.bg-red-500');
    await rejectButton.trigger('click');

    expect(accountsStore.clearMessages).toHaveBeenCalledTimes(2);
    expect(accountsStore.updateAccountStatus).toHaveBeenCalledWith(1, 'closed', expect.any(Function));
  });

  it('displays success message from store', async () => {
    accountsStore.successMessage = 'Account approved!';
    const wrapper = mount(PendingAccountsView, { global: { plugins: [pinia] } });
    await nextTick();
    expect(wrapper.text()).toContain('Account approved!');
  });

  it('displays update error message from store', async () => {
    accountsStore.updateError = 'Approval failed!';
    const wrapper = mount(PendingAccountsView, { global: { plugins: [pinia] } });
    await nextTick();
    expect(wrapper.text()).toContain('Update Failed:');
    expect(wrapper.text()).toContain('Approval failed!');
  });

  it('calls loadPendingAccounts when changePage is triggered', async () => {
    accountsStore.accounts = [{ account_id: 1, account_number: 'ACC001', status_name: 'pending_approval' }] as any;
    accountsStore.totalPages = 2;
    accountsStore.currentPage = 1;
    const wrapper = mount(PendingAccountsView, { global: { plugins: [pinia] } });
    await nextTick();

    const nextButton = wrapper.find('button:contains(Next)');
    await nextButton.trigger('click');

    expect(accountsStore.fetchAccounts).toHaveBeenCalledTimes(2); // Once on mount, once on changePage
    expect(accountsStore.fetchAccounts).toHaveBeenLastCalledWith(2, 10, { status_name: 'pending_approval' });
  });
});
```
