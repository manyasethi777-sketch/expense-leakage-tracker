document.addEventListener('DOMContentLoaded', () => {
    const leakageAmountEl = document.getElementById('leakage-amount');
    const modalOverlay = document.getElementById('intervention-modal');
    const modalAmountEl = document.getElementById('modal-amount');
    const modalSourceEl = document.getElementById('modal-source');
    const modalDescEl = document.getElementById('modal-desc');
    const modalExpenseIdEl = document.getElementById('modal-expense-id');
    const categorySelect = document.getElementById('category-select');
    const categorizeForm = document.getElementById('categorize-form');

    let isModalOpen = false;

    // Format currency
    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    };

    // Fetch initial leakage data
    const fetchLeakage = async () => {
        try {
            const res = await fetch('/api/leakage');
            const data = await res.json();
            if (data.total_wasted !== undefined && data.total_wasted !== null) {
                leakageAmountEl.textContent = formatCurrency(data.total_wasted);
            }
        } catch (error) {
            console.error('Failed to fetch leakage:', error);
        }
    };

    // Fetch categories for the dropdown
    const fetchCategories = async () => {
        try {
            const res = await fetch('/api/categories');
            const data = await res.json();
            if (data.categories) {
                data.categories.forEach(cat => {
                    const option = document.createElement('option');
                    option.value = cat.category_id;
                    option.textContent = cat.name;
                    categorySelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Failed to fetch categories:', error);
        }
    };

    // Poll for pending interventions
    const pollPendingTransactions = async () => {
        if (isModalOpen) return; // Don't poll if modal is already showing

        try {
            const res = await fetch('/api/pending_intervention');
            const data = await res.json();
            
            if (data.status === 'found' && data.transaction) {
                showModal(data.transaction);
            }
        } catch (error) {
            console.error('Failed to poll for transactions:', error);
        }
    };

    const showModal = (transaction) => {
        isModalOpen = true;
        modalAmountEl.textContent = formatCurrency(transaction.amount);
        modalSourceEl.textContent = transaction.source;
        modalDescEl.textContent = transaction.description;
        modalExpenseIdEl.value = transaction.expense_id;
        
        categorySelect.value = ''; // Reset selection
        modalOverlay.classList.remove('hidden');
    };

    const hideModal = () => {
        modalOverlay.classList.add('hidden');
        isModalOpen = false;
        fetchLeakage(); // Refresh total after categorizing
    };

    // Handle form submission
    categorizeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const expenseId = modalExpenseIdEl.value;
        const categoryId = categorySelect.value;
        
        if (!categoryId) return;
        
        try {
            const res = await fetch(`/api/expenses/${expenseId}/categorize`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ category_id: parseInt(categoryId) })
            });
            
            if (res.ok) {
                hideModal();
            } else {
                console.error('Failed to categorize');
            }
        } catch (error) {
            console.error('Error submitting category:', error);
        }
    });

    // Initialize
    fetchLeakage();
    fetchCategories();
    
    // Start short-polling every 5 seconds
    setInterval(pollPendingTransactions, 5000);
});
