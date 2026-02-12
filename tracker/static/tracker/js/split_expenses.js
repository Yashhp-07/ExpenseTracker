
document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. Get All Elements & Data ---
    const form = document.getElementById('add-expense-form');
    const amountInput = document.getElementById('amount'); 
    
    const userName = form.dataset.username;
    const userId = parseInt(form.dataset.userid);
    const friendName = form.dataset.friendname;
    const friendId = parseInt(form.dataset.friendid);

    // View Toggling
    const simpleSplitView = document.getElementById('simple-split-view');
    const advancedSplitView = document.getElementById('advanced-split-view');
    const changeSplitBtn = document.getElementById('change-split-btn');
    const fewerOptionsBtn = document.getElementById('fewer-options-btn');

    // "Paid By" Elements (NEW)
    const paidByBtn = document.getElementById('paid-by-btn');
    const payerList = document.getElementById('payer-list'); // The new dropdown
    const paidByRadios = document.querySelectorAll('input[name="paid_by_radio"]');
    
    // Advanced View Tabs
    const splitBtns = document.querySelectorAll('#split-method-tabs .nav-link');
    const splitHeading = document.getElementById('split-heading');
    const splitContent = document.getElementById('split-content');
    
    // Hidden Fields
    const paidByField = document.getElementById('paid_by_field');
    const splitMethodField = document.getElementById('split_method_field');
    const userShareField = document.getElementById('user_share_field');
    const friendShareField = document.getElementById('friend_share_field');

    // --- 2. State ---
    let currentMethod = 'equal'; // Default to split equally

    // --- 3. Helper function to get amount ---
    function getTotalAmount() {
        return parseFloat(amountInput.value) || 0;
    }

    // --- 4. View Toggling Logic ---
    changeSplitBtn.addEventListener('click', function() {
        simpleSplitView.style.display = 'none';
        advancedSplitView.style.display = 'block';
        payerList.style.display = 'none'; // Hide payer list if open
        runCurrentRender();
    });
    fewerOptionsBtn.addEventListener('click', function() {
        advancedSplitView.style.display = 'none';
        simpleSplitView.style.display = 'block';
    });

    // --- 5. "Paid By" Logic (MODIFIED) ---
    // Sets button text on initial load
    function setInitialPaidByButton() {
        const checkedRadio = document.querySelector('input[name="paid_by_radio"]:checked');
        if (checkedRadio) {
            paidByBtn.textContent = checkedRadio.dataset.name;
            paidByField.value = checkedRadio.value;
        }
    }
    
    // Toggles the dropdown
    paidByBtn.addEventListener('click', function() {
        payerList.style.display = payerList.style.display === 'none' ? 'block' : 'none';
    });

    // Handles selection from the dropdown
    paidByRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.checked) {
                paidByBtn.textContent = this.dataset.name;
                paidByField.value = this.value;
                payerList.style.display = 'none'; // Hide list after selection
            }
        });
    });

    // --- 6. Render Functions (REMOVED renderAdjust) ---
    
    function renderEqual() {
        const amount = getTotalAmount();
        splitHeading.textContent = 'Split equally';
        splitContent.innerHTML = `
            <table class="table">
                <tr><td>${userName}</td><td>Rs ${(amount/2).toFixed(2)}</td></tr>
                <tr><td>${friendName}</td><td>Rs ${(amount/2).toFixed(2)}</td></tr>
            </table>
            <div>Rs ${(amount/2).toFixed(2)}/person (2 people)</div>
        `;
        userShareField.value = (amount/2).toFixed(2);
        friendShareField.value = (amount/2).toFixed(2);
    }

    function renderExact() {
        const amount = getTotalAmount();
        splitHeading.textContent = 'Split by exact amounts';
        splitContent.innerHTML = `
            <div><label>${userName}: <input type="number" step="0.01" min="0" id="exact-user" class="form-control" style="width:100px;display:inline;"></label></div>
            <div><label>${friendName}: <input type="number" step="0.01" min="0" id="exact-friend" class="form-control" style="width:100px;display:inline;"></label></div>
            <div id="exact-summary" class="mt-2 alert alert-info">Rs 0.00 of Rs ${amount.toFixed(2)}</div>
        `;
        function updateSummary() {
            const amount = getTotalAmount();
            const userVal = parseFloat(document.getElementById('exact-user').value) || 0;
            const friendVal = parseFloat(document.getElementById('exact-friend').value) || 0;
            const total = userVal + friendVal;
            const remaining = amount - total;
            
            const summaryEl = document.getElementById('exact-summary');
            summaryEl.innerHTML = `Rs ${total.toFixed(2)} of Rs ${amount.toFixed(2)}<br>Rs ${remaining.toFixed(2)} left`;
            summaryEl.className = (remaining.toFixed(2) == '0.00') ? 'mt-2 alert alert-success' : 'mt-2 alert alert-danger';
            
            userShareField.value = userVal.toFixed(2);
            friendShareField.value = friendVal.toFixed(2);
        }
        document.getElementById('exact-user').addEventListener('input', updateSummary);
        document.getElementById('exact-friend').addEventListener('input', updateSummary);
    }

    function renderPercent() {
        splitHeading.textContent = 'Split by percentage';
        splitContent.innerHTML = `
            <div><label>${userName}: <input type="number" step="1" min="0" max="100" id="percent-user" class="form-control" style="width:80px;display:inline;"> %</label></div>
            <div><label>${friendName}: <input type="number" step="1" min="0" max="100" id="percent-friend" class="form-control" style="width:80px;display:inline;"> %</label></div>
            <div id="percent-summary" class="mt-2 alert alert-info">0% of 100%</div>
        `;
        function updateSummary() {
            const amount = getTotalAmount();
            const userVal = parseFloat(document.getElementById('percent-user').value) || 0;
            const friendVal = parseFloat(document.getElementById('percent-friend').value) || 0;
            const totalPercent = userVal + friendVal;
            const userAmt = amount * (userVal/100);
            const friendAmt = amount * (friendVal/100);
            
            const summaryEl = document.getElementById('percent-summary');
            summaryEl.innerHTML = `${totalPercent.toFixed(0)}% of 100%<br>${(100-totalPercent).toFixed(0)}% left`;
            summaryEl.className = (totalPercent.toFixed(0) == 100) ? 'mt-2 alert alert-success' : 'mt-2 alert alert-danger';

            userShareField.value = userAmt.toFixed(2);
            friendShareField.value = friendAmt.toFixed(2);
        }
        document.getElementById('percent-user').addEventListener('input', updateSummary);
        document.getElementById('percent-friend').addEventListener('input', updateSummary);
    }
    
    // 'renderAdjust' function has been removed

    function renderShares() {
        splitHeading.textContent = 'Split by shares';
        splitContent.innerHTML = `
            <div><label>${userName}: <input type="number" step="0.01" min="0" id="shares-user" class="form-control" style="width:80px;display:inline;" value="1"></label> shares</div>
            <div><label>${friendName}: <input type="number" step="0.01" min="0" id="shares-friend" class="form-control" style="width:80px;display:inline;" value="1"></label> shares</div>
            <div id="shares-summary" class="mt-2 alert alert-info"></div>
        `;
        function updateSummary() {
            const amount = getTotalAmount();
            const userShares = parseFloat(document.getElementById('shares-user').value) || 0;
            const friendShares = parseFloat(document.getElementById('shares-friend').value) || 0;
            const totalShares = userShares + friendShares;
            
            const userAmt = (totalShares > 0) ? amount * (userShares / totalShares) : 0;
            const friendAmt = (totalShares > 0) ? amount * (friendShares / totalShares) : 0;
            const perShareVal = (totalShares > 0) ? (amount / totalShares) : 0;

            let summary = `Total: ${totalShares} shares (Rs ${perShareVal.toFixed(2)} / share)<br>`;
            summary += `<b>${userName}:</b> Rs ${userAmt.toFixed(2)}<br><b>${friendName}:</b> Rs ${friendAmt.toFixed(2)}`;
            document.getElementById('shares-summary').innerHTML = summary;
            
            userShareField.value = userAmt.toFixed(2);
            friendShareField.value = friendAmt.toFixed(2);
        }
        document.getElementById('shares-user').addEventListener('input', updateSummary);
        document.getElementById('shares-friend').addEventListener('input', updateSummary);
        updateSummary();
    }

    // --- 7. Helper to run the correct render function ---
    function runCurrentRender() {
        if (currentMethod === 'equal') renderEqual();
        else if (currentMethod === 'exact') renderExact();
        else if (currentMethod === 'percent') renderPercent();
        // 'adjust' removed
        else if (currentMethod === 'shares') renderShares();
    }

    // --- 8. Advanced Tab Switching Logic ---
    splitBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            splitBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentMethod = btn.dataset.method;
            splitMethodField.value = currentMethod;
            changeSplitBtn.textContent = btn.textContent; 
            runCurrentRender();
        });
    });

    // --- 9. Listener for Amount Input ---
    amountInput.addEventListener('input', function() {
        runCurrentRender();
    });

    // --- 10. AJAX Form Submission ---
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        runCurrentRender(); 

        // Validation check (removed 'adjust')
        if (currentMethod === 'exact' && document.getElementById('exact-summary').classList.contains('alert-danger')) {
            alert('Exact amounts do not add up to the total.'); return;
        }
        if (currentMethod === 'percent' && document.getElementById('percent-summary').classList.contains('alert-danger')) {
            alert('Percentages do not add up to 100%.'); return;
        }
        
        const formData = new FormData(form);
        const url = form.action;

        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.redirect_url) {
                window.location.href = data.redirect_url;
            } else {
                alert(data.message || 'An unexpected error occurred.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error saving expense split!');
        });
    });

    // --- 11. Initial Page Load ---
    setInitialPaidByButton(); // Run the new function to set default payer
    runCurrentRender(); // Run default render ("equal")
});
