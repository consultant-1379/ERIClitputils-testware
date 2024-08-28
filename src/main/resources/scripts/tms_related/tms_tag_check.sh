#!/bin/bash
# -------------------------------------------------------------------------
#Title           :tms_tag_check.sh
#Author		 :Aileen Henry
#Date            :12:05:2016
#Usage		 :sh tms_tag_check.sh
#Description     :This script will perform the following Checks on all
#                  Testcases which contain TMS tags:
#		  1) Check for Anomolous tags
#		  2) Check that all tms_id tags are unique
#		  3) Check that tms_requirements_id contains no '_'
#                 4) Check for Missing tms tags
#		  5) Check that all tms tags are Ordered correctly
# -------------------------------------------------------------------------

## Array of Ordered TMS Tags
tms_tags[0]="@tms_id"
tms_tags[1]="@tms_requirements_id"
tms_tags[2]="@tms_title"
tms_tags[3]="@tms_description"
tms_tags[4]="@tms_test_steps"
tms_tags[5]="@tms_test_precondition"
tms_tags[6]="@tms_execution_type"

## Exclude copies of tests copied to target folder
all_filenames=$(find . -name testset*.py | grep -v target)
tms_id_ref=()
tms_req_id_ref=()
#files_not_tms_compliant=()
#files_tms_compliant=()

for filename in ${all_filenames[@]}; do
  #echo -e "\nFile: "$filename""
  all_tests_contain_tms="True"
  ## Store line numbers of all Test Function Definitions
  def_line_nos=($(grep -n "def test" $filename | cut -f1 -d:))
  array_length=${#def_line_nos[@]}
  last_pos=$((array_length - 1))

  ## For each Test method
  for i in "${!def_line_nos[@]}"; do

    ## Store the start and end lines for the Method
    if [ "${def_line_nos[$i]}" == "${def_line_nos[$last_pos]}" ]; then
       end_num=$(awk 'END {print NR}' $filename)
    else
       end_num=$((${def_line_nos["$i+1"]}-1))
    fi
    start_num="${def_line_nos[$i]}"

    ## Store the Method name
    function_name=($(awk -v lineNum=$start_num \
			'NR == lineNum {print $0}' $filename))
    ## Create array to store the Test Function TMS Failures
    function_failures=()

    ## Search for the line nos of quotes (""") ie. the method description.
    quote_line_nos=($(awk -v "line_start=$start_num" -v "line_end=$end_num" \
                   	'NR==line_start, NR==line_end'\
			 $filename | grep -n "\"\"\"" | \
                    cut -f1 -d:))
    ## If description not in double quotes check for single quotes (''')
    if [ ${#quote_line_nos[@]} -eq 0 ]; then
       quote_line_nos=($(awk -v "line_start=$start_num" -v "line_end=$end_num" \
                        'NR==line_start, NR==line_end'\
                         $filename | grep -n "'''" | \
                    cut -f1 -d:))
    fi
    for q in "${!quote_line_nos[@]}"; do
      ((quote_line_nos[$q]+=$start_num))
      ((quote_line_nos[$q]-=1))
    done

    ## Search for tms_ tags in the Method desctiption
    des_start="${quote_line_nos[0]}"
    des_end="${quote_line_nos[1]}"
    tms_search=($(awk -v "line_start=$des_start" -v "line_end=$des_end" \
               'NR==line_start, NR==line_end' $filename | grep "@tms_"))

    if [ "$tms_search" != "" ]; then

       #####################################################################
       # Check for Anomolous tags, ie. not tms/step/result                 #
       #####################################################################

       ## Store the line no.s within the method where '@' is found
       all_tags_line_nos=($(awk -v "line_start=$des_start" -v \
                           	"line_end=$des_end" \
               			'NR==line_start, NR==line_end'\
				 $filename | grep -n "@" | cut -f1 -d:))
       ## Update the line no. for each tag to its line no. within the file
       for tag in "${all_tags_line_nos[@]}"; do
         tag=$(($(( $tag + $des_start ))-1))
	 ## Store the actual line from the file
	 line_string=($(awk -v lineNum=$tag 'NR == lineNum {print $0}'\
			 $filename))
         tag_is_tms=False
	 ## Compare the line with each tms tag
         for tms_tag in "${tms_tags[@]}" ; do
           if [[ "${line_string[0]}" == *"$tms_tag"* ]]; then
              tag_is_tms=True
              break
           fi
         done
         ## Compare the line with @step/@result
         if [ "$tag_is_tms" == False ] && \
            [[ "${line_string[0]}" != *"@step:"* ]] && \
            [[ "${line_string[0]}" != *"@result:"* ]] && \
            [[ "${line_string[0]}" == *"@"* ]]; then
		function_failures+=("Anomolous Tag Found: "${line_string[0]}"")
         fi
       done

       #####################################################################
       # Check that all tms_id tags are unique                             #
       #####################################################################

       ## Store the line number of (within the method) of the tms_id tag
       tms_id_num_search=($(awk -v "line_start=$des_start" -v \
                                   "line_end=$des_end" \
                                   'NR==line_start, NR==line_end' $filename \
                                   | grep -n "@tms_id:" | cut -f1 -d:))
       ## Store the actual line number of the tms_id tag within the file
       tms_id_line_num=$(($(( $tms_id_num_search + $des_start ))-1))
       tms_id_output=($(awk -v "line_num=$tms_id_line_num" \
                             'NR==line_num {print $0} ' $filename))
       tms_id_to_check="${tms_id_output[1]}"
       ## Extract the tms_id value, which may be on the same/next line
       if [[ "${tms_id_output[0]}" == *"tms_id"* ]] && \
           [ "${tms_id_output[1]}" == "" ]; then
          next_line=($(awk -v "line_num=$(( $tms_id_line_num+1))" \
			'NR==line_num {print $0} ' $filename))
          if [[ "${next_line[0]}" != *"tms"* ]]; then
             tms_id_to_check="${next_line[0]}"
          fi
       fi
       ## Check tms_id is not duplicated
       if [ "$tms_id_to_check" != "" ]; then
          if [ ${#tms_id_ref[@]} -eq 0 ]; then
             tms_id_ref+=("$filename")
             tms_id_ref+=("TMS_ID: $tms_id_to_check")
          else
            for index in "${!tms_id_ref[@]}"; do
              duplicate_found=false
              if [[ "${tms_id_ref[$index]}" == *"TMS_ID"* ]] && \
		 [[ "${tms_id_ref[$index]}" == *"$tms_id_to_check"* ]]; then
                 duplicate_found=true
                 function_failures+=("Duplicate TMS_ID: "$tms_id_to_check"")
                 break
              fi
            done
            if [ "$duplicate_found" = false ]; then
               tms_id_ref+=("TMS_ID:$tms_id_to_check")
            fi
          fi
       fi

       #####################################################################
       # Check that tms_requirements_id contains no '_'                    #
       #####################################################################

       ## Store the tms_requirements_id tag
       tms_req_id_num_search=($(awk -v "line_start=$des_start" -v "line_end=$des_end" \
               			'NR==line_start, NR==line_end' $filename | grep -n \
					"@tms_requirements_id:" | cut -f1 -d:))
       if [ "$tms_req_id_num_search" != "" ]; then
         tms_req_line_num=$(($(( $tms_req_id_num_search + $des_start ))-1))
         tms_req_id_output=($(awk -v "line_num=$tms_req_line_num" \
				'NR==line_num {print $0} ' $filename))
         tms_req_id_to_check="${tms_req_id_output[1]}"

         if [[ "${tms_req_id_output[0]}" == *"tms_requirements_id"* ]] \
		&& [ "${tms_req_id_output[1]}" == "" ]; then
                  next_line=($(awk -v "line_num=$(( $tms_req_line_num+1))" \
				'NR==line_num {print $0} ' $filename))
          	  if [[ "${next_line[0]}" != *"tms"* ]] && [ "${next_line[0]}" != "" ]; then
             	    tms_req_id_to_check="${next_line[0]}"
          	  fi
         fi
         ## Check that the req_id doesn't contain '_'
         if [ "$tms_req_id_to_check" != "" ] && [[ "$tms_req_id_to_check" == *"_"* ]]; then
           function_failures+=("Tms_requirements_id tag contains '_': "$tms_req_id_to_check"")
         fi
       fi
       
       #####################################################################
       # Check for Missing tms tags                                        #
       #####################################################################

       ## Search for and store TMS tags
       tms_tags_in_function=()
       for line in ${tms_search[@]}; do
         if echo $line | grep -q "@tms" ; then
           line="$( cut -d ':' -f 1 <<< "$line" )"
           tms_tags_in_function+=($line)
         fi
       done

       ## Compare tags with the correct list of tms_tags
       for t in "${tms_tags[@]}"; do
         tag_found="False"
         for b in "${tms_tags_in_function[@]}"; do
           if [ "$b" == "$t" ]; then
              tag_found="True"
              break
           fi
         done
         if [ $tag_found != "True" ]; then
            function_failures+=("Tag Missing: "$t"")
            all_tags_present="False"
         fi
       done

       #####################################################################
       # Check that all tms tags are Ordered correctly                     #
       #####################################################################

       if [ "$all_tags_present" != "False" ]; then
         for index in "${!tms_tags_in_function[@]}"; do
           if [[ "${tms_tags_in_function[$index]}" != "${tms_tags[$index]}" ]] \
              || [[ "${tms_tags[$index]}" = "" ]]; then
              function_failures+=("Incorrect Tms Tag Order:"\
                                  "Tag found: '"${tms_tags_in_function[$index]}"'"\
                                  "Expected: '"${tms_tags[$index]}"'")
           fi
         done

       #####################################################################
       # Check that all step/result tms_step_tags are Ordered correctly    #
       #####################################################################

         ## Search for @tms_steps tag,@step,@result
         step_search=($(awk -v "line_start=$start_num" -v "line_end=$end_num" \
                     'NR==line_start, NR==line_end' $filename | \
                     grep '@tms_test_steps\|@step\|@result'))
         if [ "$step_search" != "" ]; then
            step_tags=()
            for ln in ${step_search[@]}; do
              if echo $ln | grep -q '@tms_test_steps\|@step\|@result' ; then
                 step_tags+=($ln)
              fi
            done
            if [[ "${step_tags[0]}" != *"${tms_tags[4]}"* ]]; then
               function_failures+=("Incorrect "${tms_tags[4]}" @step>@result\
                                    Order.")
            else
              for s in "${!step_tags[@]}"; do
                ## If the current tag is '@step', the next tag must be '@result'
                if [ $s != 0 ] && [[ "${step_tags[$s]}" == *"@step:"* ]]; then
                   if [[ "${step_tags["$s+1"]}" != *"@result:"* ]]; then
                      function_failures+=("Incorrect "${tms_tags[4]}" @step>@result Order:"\
					  " Tag '"${step_tags[$s]}"' is followed by '"${step_tags["$s+1"]}"'."\
                                           "Expected '@result'.")
                   fi
                fi
              done
            fi
         else
           function_failures+=("No Steps found under @tms_test_steps")
         fi
       fi

       #####################################################################
       # Print out all Test Function Failures                              #
       #####################################################################

       if [ "$function_failures" != "" ]; then
          file_failures+=("File: $filename Test: "${function_name[1]}"")
          echo ""
          echo "Function Name: "${function_name[1]}""
          echo The following Failures have occurred:
          for failure in "${function_failures[@]}"; do
            echo $failure
          done
       fi
    else
      #echo "No tms tags in this function."
      all_tests_contain_tms="False"
    fi
  done
  if [ $all_tests_contain_tms == "False" ]; then
     files_not_tms_compliant+=($filename)
  else
     files_tms_compliant+=($filename)
  fi
done

       #####################################################################
       # Print out Summary of Results                                      #
       #####################################################################

if [ "$file_failures" == "" ]; then
   echo TMS is Correctly Implemented in all files which contain TMS flags.
   exit 0
else
  echo -e "\nTMS has been attempted Incorrectly for the following Files/Functions:"
    for name in "${file_failures[@]}"; do
      echo $name
    done
  exit 1
fi
