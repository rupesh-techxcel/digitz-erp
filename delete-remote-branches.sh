#!/bin/bash

# Remote to target
REMOTE="upstream"

# List of branches to delete, excluding master and develop
branches=(
  AEV contracting credit_debit deep-digitz dev_11 dev_12 dev_13 dev_14 dev_15 dev_16 dev_17 dev_18
  dev_AEV dev_BR dev_COA dev_PI dev_PS_report dev_abhi dev_account dev_all_in_one dev_allocation_reports
  dev_ashna dev_checkbox dev_color dev_connections dev_date_name dev_delivery dev_delivery_report
  dev_dni dev_dnpe dev_eedt dev_entry dev_expense_entry dev_filterw dev_format_ dev_gl dev_gl_po
  dev_hidden1 dev_hrbase dev_is dev_is_new dev_item_list dev_newhr dev_newreport dev_pay
  dev_paymententry dev_pcv dev_perm dev_pl dev_pmode1 dev_postingss dev_pro dev_quotation dev_re
  dev_receiptSR dev_recepit_entry dev_recn dev_rep dev_report dev_reports dev_restore dev_rol
  dev_sale dev_src dev_stck dev_stock_balance dev_sub dev_summary dev_summary_rep dev_task10
  dev_task2021 dev_task4 dev_task45 dev_task5 dev_task6 dev_task7 dev_task8 dev_tax_report
  dev_trial dev_trialcal dev_words dev_workspace digitz-project-module digitz_dolphin
  master_deep profit_and_loss_fixex puja_changes register stock_report summary
)

# Loop and delete each one
for branch in "${branches[@]}"; do
  echo "🗑️ Deleting $branch from $REMOTE"
  git push "$REMOTE" --delete "$branch"
done

echo "✅ All specified branches deleted (except master and develop)."
