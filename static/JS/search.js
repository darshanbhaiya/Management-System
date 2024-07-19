// // Modify the searchFunction to exclude action buttons from being updated
// function searchFunction() {
//     var input, filter, table, tr, td, i, txtValue;
//     input = document.getElementById("searchInput");
//     filter = input.value.toUpperCase();
//     table = document.querySelector("table");
//     tr = table.getElementsByTagName("tr");

//     // Loop through all table rows, and hide those who don't match the search query
//     for (i = 0; i < tr.length; i++) {
//         td = tr[i].getElementsByTagName("td");
//         for (var j = 0; j < td.length; j++) {
//             if (td[j] && !td[j].classList.contains('action-cell')) { // Exclude action buttons
//                 txtValue = td[j].textContent || td[j].innerText;
//                 if (txtValue.toUpperCase().indexOf(filter) > -1) {
//                     td[j].innerHTML = txtValue.replace(new RegExp(filter, "gi"), function(match) {
//                         return '<span class="highlight">' + match + '</span>';
//                     });
//                 } else {
//                     td[j].innerHTML = txtValue;
//                 }
//             }
//         }
//     }
// }


function searchFunction() {
    var input, filter, tables, tr, td, i, j, txtValue;
    input = document.getElementById("searchInput");
    filter = input.value.toUpperCase();
    tables = document.querySelectorAll("table");

    // Loop through each table
    tables.forEach(function(table) {
        tr = table.getElementsByTagName("tr");

        // Loop through all table rows of the current table
        for (i = 0; i < tr.length; i++) {
            td = tr[i].getElementsByTagName("td");
            let found = false; // Flag to indicate if any match is found in the row

            // Loop through all cells of the current row
            for (j = 0; j < td.length; j++) {
                // Exclude action buttons from being searched
                if (!td[j].classList.contains('action-cell') && !td[j].classList.contains('password-cell')) {
                    txtValue = td[j].textContent || td[j].innerText;
                    let index = txtValue.toUpperCase().indexOf(filter);
                    if (index > -1) {
                        // If the cell content matches the search query, display the row
                        tr[i].style.display = "";
                        let highlightedText = txtValue.substring(0, index) +
                            "<span class='highlight'>" + txtValue.substring(index, index + filter.length) + "</span>" +
                            txtValue.substring(index + filter.length);
                        td[j].innerHTML = highlightedText;
                        found = true; // Set found flag to true
                    } else {
                        // If no match is found in the cell, hide the row
                        tr[i].style.display = "none";
                    }
                }
            }

            // If any match is found in the row, display it
            if (found) {
                tr[i].style.display = "";
            }
        }
    });
}
