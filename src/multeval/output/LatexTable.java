package multeval.output;

import java.io.*;
import java.util.*;

import multeval.*;
import multeval.metrics.*;
import multeval.ResultsManager.Type;

public class LatexTable {

  public void write(ResultsManager results, List<Metric<?>> metricList, PrintWriter out, boolean fullDoc) {
    if(fullDoc) {
      out.println("\\documentclass[12pt]{article}");
      out.println("\\usepackage[american]{babel}");
      out.println("\\usepackage{multirow}");
      out.println("\\usepackage{amsmath, amsthm, amssymb}");
      out.println("\\begin{document}");
    }

    out.println("\\begin{table}[htb]");
    out.println("\\begin{center}");
    out.println("\\begin{footnotesize}");
    out.println("\\begin{tabular}{|l|l|l|l|l|l|}");
    out.println("\\hline");
    out.println("\\bf Metric & \\bf System & \\bf Avg & \\bf $\\overline{s}_{\\text{sel}}$ & \\bf $s_{\\text{Test}}$ & \\bf $p$-value \\\\");
    out.println("\\hline");

    String[] metrics = results.metricNames;
    String[] systems = results.sysNames;
    int sysCount = systems.length;
    for(int iMetric = 0; iMetric < metrics.length; iMetric++) {
      String metricName = metrics[iMetric];

      String metricArrow = metricList.get(iMetric).isBiggerBetter() ? " $\\uparrow$" : " $\\downarrow$";
      // TODO: Remove this hack
      if(metricName.equals("Length")) {
        metricArrow = "";
      }
      out.println("\\multirow{" + sysCount + "}{*}{" + metricName + metricArrow + "}");
      for(int iSys = 0; iSys < sysCount; iSys++) {
        // Escape underscore chars from descriptive names
        String sysName = systems[iSys].replaceAll("_", "\\_");
        double avg = results.get(iMetric, iSys, Type.AVG);
        double sSel = results.get(iMetric, iSys, Type.RESAMPLED_STDDEV_AVG);
        double sTest = results.get(iMetric, iSys, Type.STDDEV);
        String sTestStr = Double.isNaN(sTest) ? "-" : String.format("%.1f", sTest);
        if (iSys == 0) {
          // baseline has no p-value
          out.println(String.format("& %s & %.1f & %.1f & %s & - \\\\", sysName, avg, sSel, sTestStr));
        } else {
          double p = results.get(iMetric, iSys, Type.P_VALUE);
          out.println(String.format("& %s & %.1f & %.1f & %s & %.2f \\\\", sysName, avg, sSel, sTestStr, p));
        }
      }
      out.println("\\hline");
    }

    out.println("\\end{tabular}");
    out.println("\\end{footnotesize}");
    out.println("\\end{center}");
    StringBuilder metricDescs = new StringBuilder();
    for(Metric<?> metric : metricList) {
      metricDescs.append(metric.getMetricDescription() + "; ");
    }
    out.println("\\caption{\\label{tab:scores} Metric scores for all systems: "+metricDescs.toString()+". p-values are relative to baseline and indicate whether a difference of this magnitude (between the baseline and the system on that line) is likely to be generated again by some random process (a randomized optimizer). Metric scores are averages over multiple runs. $s_{sel}$ indicates the variance due to test set selection and has nothing to do with optimizer instability.}");
    out.println("\\end{table}");

    if(fullDoc) {
      out.println("\\end{document}");
    }
    out.flush();
  }

  public void writeMetricsAsCols(ResultsManager results, List<Metric<?>> metricList, PrintWriter out, boolean fullDoc) {
    if(fullDoc) {
      out.println("\\documentclass[12pt]{article}");
      out.println("\\usepackage[american]{babel}");
      out.println("\\usepackage{multirow}");
      out.println("\\usepackage{amsmath, amsthm, amssymb}");
      out.println("\\begin{document}");
    }

    out.println("\\begin{table*}[htb]");
    out.println("\\begin{center}");
    out.println("\\begin{footnotesize}");

    String[] metrics = results.metricNames;
    String[] systems = results.sysNames;

    StringBuilder sbTabHeader = new StringBuilder("\\begin{tabular}{l");
    StringBuilder sbHeader = new StringBuilder("\\bf Systems");

    for(int iMetric = 0; iMetric < metrics.length; iMetric++) {
      String metricName = metrics[iMetric];
      String metricArrow = metricList.get(iMetric).isBiggerBetter() ? " $\\uparrow$" : " $\\downarrow$";
      // TODO: Remove this hack
      if(metricName.equals("Length")) {
        metricArrow = "";
      }
      //sbHeader.append(" & \\multicolumn{2}{|c}{ \\bf ").append(metricName).append(metricArrow).append("}");
      sbHeader.append(" & \\bf ").append(metricArrow).append(metricName).append(" ($\\sigma$/p)");
      //out.print(" & \\multicolumn{4}{|c}{ \\bf "+metricName+metricArrow+"}");
      //sbTabHeader.append("|c|c|c|c");
      sbTabHeader.append("|l");
    }
    out.println(sbTabHeader.append("}").toString());
    out.println("\\hline");
    out.println(sbHeader.append("\\\\").toString());
    out.println("\\hline");

    int sysCount = systems.length;
    for(int iSys = 0; iSys < sysCount; iSys++) {
        // Escape underscore chars from descriptive names
        String sysName = systems[iSys].replaceAll("_", "\\_");
        out.print(String.format(" %s ", sysName));
        for(int iMetric = 0; iMetric < metrics.length; iMetric++) {

            double avg = results.get(iMetric, iSys, Type.AVG);
            double sSel = results.get(iMetric, iSys, Type.RESAMPLED_STDDEV_AVG);
            double sTest = results.get(iMetric, iSys, Type.STDDEV);
            String sTestStr = Double.isNaN(sTest) ? "-" : String.format("%.1f", sTest);
            if (iSys == 0) {
              // baseline has no p-value
              //out.print(String.format("& %.1f & %.1f & %s & - ", avg, sSel, sTestStr)); // 4 columns 
              //out.print(String.format("& %.1f & - ", avg)); // 2 columns with avg and p-value
              //out.print(String.format("& %.1f (%.1f/%s/-) ", avg, sSel, sTestStr)); // 1 column
              out.print(String.format("& %.1f (%s/-) ", avg, sTestStr)); // 1 column with avg, stddev and p-value
            } else {
              double p = results.get(iMetric, iSys, Type.P_VALUE);
              //out.print(String.format("& %.1f & %.1f & %s & %.2f ", avg, sSel, sTestStr, p)); // 4 columns
              //out.print(String.format("& %.1f & %.2f ", avg, p)); // 2 coumns with avg and p-value
              //out.print(String.format("& %.1f (%.1f/%s/%.2f) ", avg, sSel, sTestStr, p)); // 1 column
              out.print(String.format("& %.1f (%s/%.2f) ", avg, sTestStr, p)); // 1 column with avg, stddev and p-value
            }
        }
        out.println("\\\\");
        //out.println("\\hline");
    }

    out.println("\\end{tabular}");
    out.println("\\end{footnotesize}");
    out.println("\\end{center}");
    StringBuilder metricDescs = new StringBuilder();
    for(Metric<?> metric : metricList) {
      metricDescs.append(metric.getMetricDescription() + "; ");
    }
    out.println("\\caption{\\label{tab:scores} Metric scores for all systems: "+metricDescs.toString()+". p-values are relative to baseline and indicate whether a difference of this magnitude (between the baseline and the system on that line) is likely to be generated again by some random process (a randomized optimizer). Metric scores are averages over multiple runs. $s_{sel}$ indicates the variance due to test set selection and has nothing to do with optimizer instability.}");
    out.println("\\end{table*}");

    if(fullDoc) {
      out.println("\\end{document}");
    }
    out.flush();
  }
}
