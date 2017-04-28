package multeval;

import java.util.*;

public class ResultsManager {

  // indices: iSys, iMetric
  private final List<List<Map<Type, Double>>> resultsBySys;
  private int numMetrics;
  public final String[] metricNames;
  public final String[] sysNames;
  public final int numOptRuns;

  public enum Type {
    AVG, STDDEV, MIN, MAX, RESAMPLED_MEAN_AVG, RESAMPLED_STDDEV_AVG, RESAMPLED_MIN, RESAMPLED_MAX, P_VALUE, MEDIAN,
    MEDIAN_IDX
  }

  public ResultsManager(String[] metricNames, String[] sysNames, int numOptRuns) {
    this.metricNames = metricNames;
    this.sysNames = sysNames;
    this.numOptRuns = numOptRuns;

    this.numMetrics = metricNames.length;
    int numSys = sysNames.length;
    this.resultsBySys = new ArrayList<List<Map<Type, Double>>>(numSys);
  }

  public void report(int iMetric, int iSys, Type type, double d) {
    while(resultsBySys.size() <= iSys) {
      resultsBySys.add(new ArrayList<Map<Type, Double>>(numMetrics));
    }
    List<Map<Type, Double>> resultsByMetric = resultsBySys.get(iSys);
    while(resultsByMetric.size() <= iMetric) {
      resultsByMetric.add(new HashMap<Type, Double>());
    }
    Map<Type, Double> map = resultsByMetric.get(iMetric);
    map.put(type, d);
  }

  public Double get(int iMetric, int iSys, Type type) {
    List<Map<Type, Double>> resultsByMetric = resultsBySys.get(iSys);
    if (resultsByMetric == null) {
      throw new RuntimeException("No results found for system + " + iSys);
    }
    Map<Type, Double> resultsByType = resultsByMetric.get(iMetric);
    if (resultsByType == null) {
      throw new RuntimeException("No results found for system " + iSys + " for metric " + iMetric);
    }
    Double result = resultsByType.get(type);
    if (result == null) {
      throw new RuntimeException("No results found for system " + iSys + " for metric " + iMetric + " of type " + type);
    }
    return result;
  }
}
