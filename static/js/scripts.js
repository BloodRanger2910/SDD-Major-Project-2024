// scripts.js

document.addEventListener("DOMContentLoaded", function () {
    // Add event listener for dismissing flash messages
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function (flash) {
        setTimeout(() => {
            flash.style.display = 'none';
        }, 3000); // Hide flash message after 3 seconds
    });
});

function togglePassword(inputId, iconId) {
    const passwordInput = document.getElementById(inputId);
    const icon = document.getElementById(iconId);
    if (passwordInput.type === "password") {
        passwordInput.type = "text";
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        passwordInput.type = "password";
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

document.addEventListener("DOMContentLoaded", function () {
    // Load debt summary data and render chart
    fetch('/debt_summary')
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('debtChart').getContext('2d');
            const labels = data.map(debt => debt.name);
            const initialAmounts = data.map(debt => debt.initial_amount);
            const remainingAmounts = data.map(debt => debt.remaining_amount);
            const paidOffAmounts = initialAmounts.map((initial, index) => initial - remainingAmounts[index]);

            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Initial Amount',
                            data: initialAmounts,
                            backgroundColor: 'rgba(255, 99, 132, 0.2)',
                            borderColor: 'rgba(255, 99, 132, 1)',
                            borderWidth: 1
                        },
                        {
                            label: 'Paid Off Amount',
                            data: paidOffAmounts,
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        },
                        {
                            label: 'Remaining Amount',
                            data: remainingAmounts,
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        });
});

document.addEventListener("DOMContentLoaded", function () {
    // Load expense data and render chart
    fetch('/expense_summary')
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('expenseChart').getContext('2d');
            const labels = data.map(expense => expense.category);
            const amounts = data.map(expense => expense.amount);

            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Expense Amount',
                        data: amounts,
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        });
});
