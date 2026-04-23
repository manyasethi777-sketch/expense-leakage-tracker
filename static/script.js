document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const totalSpentEl = document.getElementById('total-spent');
    const totalWastedEl = document.getElementById('total-wasted');
    const remainingBudgetEl = document.getElementById('remaining-budget');
    const budgetCardEl = document.getElementById('budget-card');
    const expenseTableBody = document.getElementById('expense-table-body');
    
    // Modal Elements
    const modalOverlay = document.getElementById('intervention-modal');
    const modalAmountEl = document.getElementById('modal-amount');
    const modalSourceEl = document.getElementById('modal-source');
    const modalDescEl = document.getElementById('modal-desc');
    const modalExpenseIdEl = document.getElementById('modal-expense-id');
    const categorySelect = document.getElementById('category-select');
    const categorizeForm = document.getElementById('categorize-form');

    let isModalOpen = false;
    let donutChart = null;

    // Format currency (INR)
    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR'
        }).format(amount);
    };

    // Initialize Chart.js
    const initOrUpdateChart = (essential, wasted, remaining) => {
        const remainingToDisplay = Math.max(0, remaining);
        const ctx = document.getElementById('spendingChart').getContext('2d');
        
        if (donutChart) {
            donutChart.data.datasets[0].data = [essential, wasted, remainingToDisplay];
            donutChart.update();
            return;
        }

        donutChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Essential Spending', 'Wasted (Leakage)', 'Unspent Budget'],
                datasets: [{
                    data: [essential, wasted, remainingToDisplay],
                    backgroundColor: [
                        '#10b981', // green for essential
                        '#ef4444', // red for leakage
                        '#334155'  // slate/gray for unspent budget
                    ],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#94a3b8',
                            font: { family: "'Inter', sans-serif" }
                        }
                    }
                }
            }
        });
    };

    // Fetch and render dashboard data
    const fetchDashboardData = async () => {
        try {
            const res = await fetch('/api/dashboard_data');
            const data = await res.json();
            
            if (data.error) throw new Error(data.error);

            const spent = parseFloat(data.total_spent) || 0;
            const wasted = parseFloat(data.total_wasted) || 0;
            const limit = parseFloat(data.budget_limit) || 0;
            const essential = spent - wasted;
            const remaining = limit - spent;

            // Update Summary Cards
            totalSpentEl.textContent = formatCurrency(spent);
            totalWastedEl.textContent = formatCurrency(wasted);
            remainingBudgetEl.textContent = formatCurrency(remaining);

            // Budget Logic
            if (remaining < 0) {
                budgetCardEl.classList.add('over-budget');
            } else {
                budgetCardEl.classList.remove('over-budget');
            }

            // Update Chart
            initOrUpdateChart(essential, wasted, remaining);

            // Populate Table
            renderTable(data.all_expenses || []);

        } catch (error) {
            console.error('Failed to fetch dashboard data:', error);
        }
    };

    const renderTable = (expenses) => {
        expenseTableBody.innerHTML = '';
        
        if (expenses.length === 0) {
            expenseTableBody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#94a3b8">No expenses found.</td></tr>';
            return;
        }

        expenses.forEach(exp => {
            const row = document.createElement('tr');
            
            const badgeClass = exp.is_essential ? 'badge-essential' : 'badge-leakage';
            const badgeText = exp.is_essential ? 'Essential' : 'Leakage';
            
            row.innerHTML = `
                <td>${exp.date || '--'}</td>
                <td>${exp.description || '--'}</td>
                <td>${exp.category_name || '--'}</td>
                <td style="font-weight: 600;">${formatCurrency(exp.amount)}</td>
                <td><span class="badge ${badgeClass}">${badgeText}</span></td>
            `;
            expenseTableBody.appendChild(row);
        });
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
        if (isModalOpen) return;

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
        modalSourceEl.textContent = transaction.source || '--';
        modalDescEl.textContent = transaction.description || '--';
        modalExpenseIdEl.value = transaction.expense_id;
        
        categorySelect.value = ''; // Reset selection
        modalOverlay.classList.remove('hidden');
    };

    const hideModal = () => {
        modalOverlay.classList.add('hidden');
        isModalOpen = false;
        fetchDashboardData(); // Refresh dashboard data after categorizing
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
                headers: { 'Content-Type': 'application/json' },
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

    // Initialize Dashboard
    fetchDashboardData();
    fetchCategories();
    
    // Start short-polling every 5 seconds
    setInterval(pollPendingTransactions, 5000);

    // Budget Modal Logic
    const budgetModal = document.getElementById('budget-modal');
    const budgetForm = document.getElementById('budget-form');
    const newBudgetInput = document.getElementById('new-budget-input');
    const cancelBudgetBtn = document.getElementById('cancel-budget-btn');

    budgetCardEl.addEventListener('click', () => {
        budgetModal.classList.remove('hidden');
    });

    cancelBudgetBtn.addEventListener('click', () => {
        budgetModal.classList.add('hidden');
    });

    budgetForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const newLimit = parseFloat(newBudgetInput.value);
        if (isNaN(newLimit)) return;

        try {
            const res = await fetch('/api/budget', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ monthly_limit: newLimit })
            });

            if (res.ok) {
                budgetModal.classList.add('hidden');
                newBudgetInput.value = '';
                fetchDashboardData(); // Refresh to show new budget
            } else {
                console.error('Failed to update budget');
            }
        } catch (error) {
            console.error('Error updating budget:', error);
        }
    });
});
