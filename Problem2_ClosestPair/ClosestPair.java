
import java.util.*;
import java.io.*;
import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.awt.geom.*;
import java.util.List;

public class ClosestPair {

    static final long SEED = 42;
    static final Color BG = new Color(235, 245, 253);
    static final Color BLUE = new Color(48, 126, 190);
    static final Color DARK = new Color(27, 61, 91);
    static final Color ORANGE = new Color(245, 137, 54);
    static final Color GREEN = new Color(54, 157, 113);

    static class Point {
        double x, y;
        int id, rankX;

        Point(double x, double y, int id) {
            this.x = x;
            this.y = y;
            this.id = id;
        }
    }

    static class Result {
        Point p1, p2;
        double distanceSquared;

        Result(Point a, Point b) {
            p1 = a;
            p2 = b;
            distanceSquared = dist2(a, b);
        }

        double distance() {
            return Math.sqrt(distanceSquared);
        }
    }

    static class Benchmark {
        int size;
        double brute, divide;

        Benchmark(int size, double brute, double divide) {
            this.size = size;
            this.brute = brute;
            this.divide = divide;
        }
    }

    static double dist2(Point a, Point b) {
        double dx = a.x - b.x;
        double dy = a.y - b.y;
        return dx * dx + dy * dy;
    }

    // Brute Force: O(n^2)
    static Result bruteForce(Point[] points) {
        if (points.length < 2) return null;

        Result best = null;

        for (int i = 0; i < points.length; i++) {
            for (int j = i + 1; j < points.length; j++) {
                double d = dist2(points[i], points[j]);

                if (best == null || d < best.distanceSquared) {
                    best = new Result(points[i], points[j]);
                }
            }
        }

        return best;
    }

    // Divide and Conquer: O(n log n)
    static Result divideAndConquer(Point[] points) {
        if (points.length < 2) {
            throw new IllegalArgumentException(
                "At least two points are required."
            );
        }

        Point[] byX = points.clone();

        Arrays.sort(byX,
            Comparator.comparingDouble((Point p) -> p.x)
                .thenComparingDouble(p -> p.y)
                .thenComparingInt(p -> p.id));

        for (int i = 0; i < byX.length; i++) {
            byX[i].rankX = i;
        }

        Point[] byY = points.clone();

        Arrays.sort(byY,
            Comparator.comparingDouble((Point p) -> p.y)
                .thenComparingDouble(p -> p.x)
                .thenComparingInt(p -> p.id));

        return solve(byX, byY, 0, byX.length);
    }

    static Result solve(Point[] byX, Point[] byY, int left, int right) {
        int n = right - left;

        if (n <= 3) {
            return bruteForce(Arrays.copyOfRange(byX, left, right));
        }

        int mid = left + n / 2;
        double midX = byX[mid].x;

        Point[] leftY = new Point[mid - left];
        Point[] rightY = new Point[right - mid];

        int li = 0, ri = 0;

        for (Point p : byY) {
            if (p.rankX >= left && p.rankX < mid) {
                leftY[li++] = p;
            } else if (p.rankX >= mid && p.rankX < right) {
                rightY[ri++] = p;
            }
        }

        Result a = solve(byX, leftY, left, mid);
        Result b = solve(byX, rightY, mid, right);

        Result best =
            a.distanceSquared <= b.distanceSquared ? a : b;

        ArrayList<Point> strip = new ArrayList<>();

        for (Point p : byY) {
            double dx = p.x - midX;

            if (p.rankX >= left && p.rankX < right
                    && dx * dx < best.distanceSquared) {
                strip.add(p);
            }
        }

        for (int i = 0; i < strip.size(); i++) {
            for (int j = i + 1; j < strip.size(); j++) {
                Point p = strip.get(i);
                Point q = strip.get(j);

                double dy = q.y - p.y;

                if (dy * dy >= best.distanceSquared) break;

                double d = dist2(p, q);

                if (d < best.distanceSquared) {
                    best = new Result(p, q);
                }
            }
        }

        return best;
    }

    static Point[] generatePoints(int n, long seed) {
        Random random = new Random(seed);
        Point[] points = new Point[n];

        for (int i = 0; i < n; i++) {
            points[i] = new Point(
                random.nextDouble() * 1000,
                random.nextDouble() * 1000,
                i + 1
            );
        }

        return points;
    }

    static double timeBrute(Point[] points) {
        long start = System.nanoTime();
        bruteForce(points);
        return (System.nanoTime() - start) / 1_000_000.0;
    }

    static double timeDivide(Point[] points) {
        long start = System.nanoTime();
        divideAndConquer(points);
        return (System.nanoTime() - start) / 1_000_000.0;
    }

    // -----------------------------------------------------
    // POINT VISUALIZATION
    // -----------------------------------------------------

    static class PointPanel extends JPanel {
        Point[] points = new Point[0];
        Result result;

        PointPanel() {
            setBackground(Color.WHITE);
            setPreferredSize(new Dimension(700, 500));
        }

        void updateData(Point[] points, Result result) {
            this.points = points;
            this.result = result;
            repaint();
        }

        protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics);

            Graphics2D g = (Graphics2D) graphics.create();
            g.setRenderingHint(
                RenderingHints.KEY_ANTIALIASING,
                RenderingHints.VALUE_ANTIALIAS_ON
            );

            int left = 65, right = 30, top = 45, bottom = 55;
            int w = getWidth() - left - right;
            int h = getHeight() - top - bottom;

            g.setColor(DARK);
            g.setFont(new Font("Segoe UI", Font.BOLD, 18));
            g.drawString("Point Distribution", left, 25);

            if (points.length == 0) {
                g.drawString("Generate or add points to begin.", left, 80);
                g.dispose();
                return;
            }

            double minX = points[0].x, maxX = points[0].x;
            double minY = points[0].y, maxY = points[0].y;

            for (Point p : points) {
                minX = Math.min(minX, p.x);
                maxX = Math.max(maxX, p.x);
                minY = Math.min(minY, p.y);
                maxY = Math.max(maxY, p.y);
            }

            double padX = Math.max(1, (maxX - minX) * 0.10);
            double padY = Math.max(1, (maxY - minY) * 0.10);

            minX -= padX;
            maxX += padX;
            minY -= padY;
            maxY += padY;

            double rangeX = Math.max(1, maxX - minX);
            double rangeY = Math.max(1, maxY - minY);

            // Grid
            g.setStroke(new BasicStroke(1));
            g.setColor(new Color(225, 235, 244));

            for (int i = 0; i <= 5; i++) {
                int x = left + i * w / 5;
                int y = top + i * h / 5;

                g.drawLine(x, top, x, top + h);
                g.drawLine(left, y, left + w, y);
            }

            g.setColor(DARK);
            g.drawRect(left, top, w, h);
            g.setFont(new Font("Segoe UI", Font.PLAIN, 11));
            g.drawString("X coordinate", left + w / 2 - 35, top + h + 35);
            g.drawString("Y", 30, top + h / 2);

            // Draw all points
            g.setColor(BLUE);

            for (Point p : points) {
                int x = left + (int) ((p.x - minX) / rangeX * w);
                int y = top + h - (int) ((p.y - minY) / rangeY * h);

                g.fillOval(x - 4, y - 4, 8, 8);
            }

            // Highlight the closest pair
            if (result != null) {
                int x1 = left + (int) ((result.p1.x - minX) / rangeX * w);
                int y1 = top + h - (int) ((result.p1.y - minY) / rangeY * h);

                int x2 = left + (int) ((result.p2.x - minX) / rangeX * w);
                int y2 = top + h - (int) ((result.p2.y - minY) / rangeY * h);

                g.setColor(ORANGE);
                g.setStroke(new BasicStroke(3));
                g.drawLine(x1, y1, x2, y2);

                g.fillOval(x1 - 7, y1 - 7, 14, 14);
                g.fillOval(x2 - 7, y2 - 7, 14, 14);

                g.setColor(DARK);
                g.setFont(new Font("Segoe UI", Font.BOLD, 12));
                g.drawString("P" + result.p1.id, x1 + 8, y1 - 8);
                g.drawString("P" + result.p2.id, x2 + 8, y2 - 8);
            }

            g.dispose();
        }
    }

    // -----------------------------------------------------
    // BENCHMARK CHART
    // -----------------------------------------------------

    static class ChartPanel extends JPanel {
        List<Benchmark> data = new ArrayList<>();

        ChartPanel() {
            setBackground(Color.WHITE);
            setPreferredSize(new Dimension(700, 500));
        }

        void updateData(List<Benchmark> data) {
            this.data = data;
            repaint();
        }

        protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics);
            Graphics2D g = (Graphics2D) graphics.create();

            g.setRenderingHint(
                RenderingHints.KEY_ANTIALIASING,
                RenderingHints.VALUE_ANTIALIAS_ON
            );

            int left = 65, top = 60;
            int width = getWidth() - 100;
            int height = getHeight() - 150;

            g.setColor(DARK);
            g.setFont(new Font("Segoe UI", Font.BOLD, 18));
            g.drawString("Algorithm Performance Comparison", left, 30);

            if (data.isEmpty()) {
                g.setFont(new Font("Segoe UI", Font.PLAIN, 14));
                g.drawString(
                    "Click Benchmark to compare execution times.",
                    left, 85
                );
                g.dispose();
                return;
            }

            double max = 0.001;

            for (Benchmark b : data) {
                max = Math.max(max, Math.max(b.brute, b.divide));
            }

            max *= 1.15;

            // Horizontal grid lines and labels
            for (int i = 0; i <= 5; i++) {
                int y = top + height - i * height / 5;

                g.setColor(new Color(225, 235, 244));
                g.drawLine(left, y, left + width, y);

                g.setColor(DARK);
                g.setFont(new Font("Segoe UI", Font.PLAIN, 10));
                g.drawString(
                    String.format(Locale.US, "%.3f", max * i / 5),
                    8, y + 4
                );
            }

            int groupWidth = width / data.size();
            int barWidth = Math.min(28, Math.max(8, groupWidth / 4));

            for (int i = 0; i < data.size(); i++) {
                Benchmark b = data.get(i);
                int center = left + i * groupWidth + groupWidth / 2;

                int bh = (int) (b.brute / max * height);
                int dh = (int) (b.divide / max * height);

                g.setColor(BLUE);
                g.fillRoundRect(
                    center - barWidth - 2,
                    top + height - bh,
                    barWidth, Math.max(1, bh), 5, 5
                );

                g.setColor(ORANGE);
                g.fillRoundRect(
                    center + 2,
                    top + height - dh,
                    barWidth, Math.max(1, dh), 5, 5
                );

                g.setColor(DARK);
                g.setFont(new Font("Segoe UI", Font.PLAIN, 11));
                g.drawString(
                    String.valueOf(b.size),
                    center - 18, top + height + 20
                );
            }

            g.setColor(BLUE);
            g.fillRect(left, getHeight() - 45, 13, 13);
            g.setColor(DARK);
            g.drawString("Brute Force", left + 20, getHeight() - 34);

            g.setColor(ORANGE);
            g.fillRect(left + 135, getHeight() - 45, 13, 13);
            g.setColor(DARK);
            g.drawString(
                "Divide & Conquer", left + 155, getHeight() - 34
            );

            g.dispose();
        }
    }

    // -----------------------------------------------------
    // APPLICATION
    // -----------------------------------------------------

    static class App {
        JFrame frame;
        PointPanel pointPanel = new PointPanel();
        ChartPanel chartPanel = new ChartPanel();

        ArrayList<Point> points = new ArrayList<>();
        Result result;

        JLabel countLabel = new JLabel("Points: 0");
        JLabel pairLabel = new JLabel("Closest pair: Not calculated");
        JLabel distanceLabel = new JLabel("Minimum distance: —");
        JLabel bruteLabel = new JLabel("Brute Force: —");
        JLabel divideLabel = new JLabel("Divide & Conquer: —");
        JLabel statusLabel = new JLabel("Ready");

        int nextId = 1;
        long seed = SEED;

        App() {
            frame = new JFrame("Closest Pair of Points | Algorithm Lab");
            frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
            frame.setSize(1100, 780);
            frame.setMinimumSize(new Dimension(850, 650));
            frame.getContentPane().setBackground(BG);
            frame.setLayout(new BorderLayout(10, 10));

            buildHeader();
            buildControls();
            buildContent();
            buildFooter();

            generateRandomPoints(100);
            frame.setLocationRelativeTo(null);
            frame.setVisible(true);
        }

        void buildHeader() {
            JPanel header = new JPanel();
            header.setBackground(new Color(214, 233, 250));
            header.setLayout(new BoxLayout(header, BoxLayout.Y_AXIS));
            header.setBorder(new EmptyBorder(14, 18, 14, 18));

            JLabel title = new JLabel("CLOSEST PAIR OF POINTS");
            title.setFont(new Font("Segoe UI", Font.BOLD, 23));
            title.setForeground(DARK);
            title.setAlignmentX(Component.LEFT_ALIGNMENT);

            JLabel subtitle = new JLabel(
                "Visualize, compare and understand computational geometry algorithms"
            );
            subtitle.setFont(new Font("Segoe UI", Font.PLAIN, 12));
            subtitle.setForeground(new Color(67, 103, 131));
            subtitle.setAlignmentX(Component.LEFT_ALIGNMENT);

            header.add(title);
            header.add(Box.createVerticalStrut(4));
            header.add(subtitle);

            frame.add(header, BorderLayout.NORTH);
        }

        JButton button(String text, Runnable action) {
            JButton b = new JButton(text);
            b.setFont(new Font("Segoe UI", Font.BOLD, 11));
            b.setForeground(Color.WHITE);
            b.setBackground(BLUE);
            b.setFocusPainted(false);
            b.setBorderPainted(false);
            b.setCursor(new Cursor(Cursor.HAND_CURSOR));
            b.setMargin(new Insets(9, 12, 9, 12));

            b.addActionListener(e -> action.run());
            return b;
        }

        void buildControls() {
            JPanel controls = new JPanel(new FlowLayout(FlowLayout.LEFT, 7, 8));
            controls.setBackground(BG);
            controls.setBorder(new EmptyBorder(0, 10, 0, 10));

            controls.add(button("Generate Points", () -> askGenerate()));
            controls.add(button("Add Point", () -> addPoint()));
            controls.add(button("Remove Point", () -> removePoint()));
            controls.add(button("Find Closest Pair", () -> findClosest()));
            controls.add(button("Benchmark", () -> runBenchmark()));
            controls.add(button("Export CSV", () -> exportCSV()));
            controls.add(button("Reset", () -> reset()));

            frame.add(controls, BorderLayout.PAGE_START);
        }

        void buildContent() {
            JTabbedPane tabs = new JTabbedPane();
            tabs.setFont(new Font("Segoe UI", Font.BOLD, 12));

            tabs.addTab("Point Visualization", pointPanel);
            tabs.addTab("Performance Chart", chartPanel);

            JPanel results = new JPanel();
            results.setLayout(new BoxLayout(results, BoxLayout.Y_AXIS));
            results.setBackground(new Color(248, 251, 254));
            results.setBorder(new EmptyBorder(15, 15, 15, 15));
            results.setPreferredSize(new Dimension(245, 250));

            JLabel heading = new JLabel("RESULTS");
            heading.setFont(new Font("Segoe UI", Font.BOLD, 15));
            heading.setForeground(DARK);

            results.add(heading);
            results.add(Box.createVerticalStrut(12));

            addResult(results, countLabel);
            addResult(results, pairLabel);
            addResult(results, distanceLabel);
            addResult(results, bruteLabel);
            addResult(results, divideLabel);

            JLabel complexity = new JLabel(
                "<html><b>Time complexity</b><br><br>" +
                "Brute Force: O(n²)<br>" +
                "Divide & Conquer: O(n log n)</html>"
            );
            complexity.setFont(new Font("Segoe UI", Font.PLAIN, 12));
            complexity.setForeground(DARK);
            complexity.setBorder(new EmptyBorder(15, 0, 0, 0));
            results.add(complexity);

            JPanel center = new JPanel(new BorderLayout(10, 0));
            center.setBackground(BG);
            center.setBorder(new EmptyBorder(0, 10, 5, 10));
            center.add(tabs, BorderLayout.CENTER);
            center.add(results, BorderLayout.EAST);

            frame.add(center, BorderLayout.CENTER);
        }

        void addResult(JPanel panel, JLabel label) {
            label.setFont(new Font("Segoe UI", Font.PLAIN, 12));
            label.setForeground(DARK);
            label.setAlignmentX(Component.LEFT_ALIGNMENT);
            label.setBorder(new EmptyBorder(7, 0, 7, 0));
            panel.add(label);
        }

        void buildFooter() {
            JPanel footer = new JPanel(new BorderLayout());
            footer.setBackground(new Color(214, 233, 250));
            footer.setBorder(new EmptyBorder(8, 15, 8, 15));

            statusLabel.setFont(new Font("Segoe UI", Font.PLAIN, 11));
            statusLabel.setForeground(DARK);
            footer.add(statusLabel, BorderLayout.WEST);

            JLabel legend = new JLabel("Blue: points   Orange: closest pair");
            legend.setFont(new Font("Segoe UI", Font.PLAIN, 11));
            legend.setForeground(DARK);
            footer.add(legend, BorderLayout.EAST);

            frame.add(footer, BorderLayout.SOUTH);
        }

        void askGenerate() {
            String input = JOptionPane.showInputDialog(
                frame,
                "How many random points would you like? (2–5000)",
                "100"
            );

            if (input == null) return;

            try {
                int n = Integer.parseInt(input.trim());

                if (n < 2 || n > 5000) {
                    throw new NumberFormatException();
                }

                generateRandomPoints(n);
            } catch (NumberFormatException e) {
                JOptionPane.showMessageDialog(
                    frame,
                    "Enter a whole number between 2 and 5000.",
                    "Invalid input",
                    JOptionPane.WARNING_MESSAGE
                );
            }
        }

        void generateRandomPoints(int n) {
            points.clear();

            Point[] generated = generatePoints(n, seed++);
            nextId = 1;

            for (Point p : generated) {
                p.id = nextId++;
                points.add(p);
            }

            result = null;
            updateView();
            clearResults();

            statusLabel.setText(
                "Generated " + n + " random points. Find the closest pair."
            );
        }

        void addPoint() {
            JTextField xField = new JTextField();
            JTextField yField = new JTextField();

            JPanel panel = new JPanel(new GridLayout(2, 2, 8, 8));
            panel.add(new JLabel("X coordinate:"));
            panel.add(xField);
            panel.add(new JLabel("Y coordinate:"));
            panel.add(yField);

            int answer = JOptionPane.showConfirmDialog(
                frame, panel, "Add a Point",
                JOptionPane.OK_CANCEL_OPTION
            );

            if (answer != JOptionPane.OK_OPTION) return;

            try {
                double x = Double.parseDouble(xField.getText().trim());
                double y = Double.parseDouble(yField.getText().trim());

                if (!Double.isFinite(x) || !Double.isFinite(y)) {
                    throw new NumberFormatException();
                }

                points.add(new Point(x, y, nextId++));
                result = null;

                updateView();
                clearResults();
                statusLabel.setText("Point added. Find the closest pair.");
            } catch (NumberFormatException e) {
                JOptionPane.showMessageDialog(
                    frame,
                    "Enter valid finite numbers for both coordinates.",
                    "Invalid coordinates",
                    JOptionPane.WARNING_MESSAGE
                );
            }
        }

        void removePoint() {
            if (points.size() <= 2) {
                JOptionPane.showMessageDialog(
                    frame,
                    "At least two points are required.",
                    "Cannot remove point",
                    JOptionPane.WARNING_MESSAGE
                );
                return;
            }

            String[] choices = new String[points.size()];

            for (int i = 0; i < points.size(); i++) {
                Point p = points.get(i);
                choices[i] = String.format(
                    Locale.US, "P%d  (%.3f, %.3f)", p.id, p.x, p.y
                );
            }

            String choice = (String) JOptionPane.showInputDialog(
                frame, "Choose a point to remove:",
                "Remove Point", JOptionPane.QUESTION_MESSAGE,
                null, choices, choices[0]
            );

            if (choice == null) return;

            int index = Arrays.asList(choices).indexOf(choice);

            if (index >= 0) {
                points.remove(index);
                result = null;
                updateView();
                clearResults();
                statusLabel.setText("Point removed.");
            }
        }

        void findClosest() {
            if (points.size() < 2) {
                JOptionPane.showMessageDialog(
                    frame, "Add at least two points first."
                );
                return;
            }

            Point[] data = points.toArray(new Point[0]);

            long start = System.nanoTime();
            Result brute = bruteForce(data);
            double bruteTime =
                (System.nanoTime() - start) / 1_000_000.0;

            start = System.nanoTime();
            result = divideAndConquer(data);
            double divideTime =
                (System.nanoTime() - start) / 1_000_000.0;

            boolean correct = Math.abs(
                brute.distance() - result.distance()
            ) < 1e-9;

            countLabel.setText("Points: " + points.size());

            pairLabel.setText(String.format(
                "Closest pair: P%d and P%d",
                result.p1.id, result.p2.id
            ));

            distanceLabel.setText(String.format(
                Locale.US, "Minimum distance: %.6f",
                result.distance()
            ));

            bruteLabel.setText(String.format(
                Locale.US, "Brute Force: %.3f ms", bruteTime
            ));

            divideLabel.setText(String.format(
                Locale.US, "Divide & Conquer: %.3f ms", divideTime
            ));

            updateView();

            statusLabel.setText(
                "Correctness check: " + (correct ? "PASS" : "FAIL")
            );
        }

        void runBenchmark() {
            statusLabel.setText("Running benchmark...");
            frame.setCursor(Cursor.getPredefinedCursor(Cursor.WAIT_CURSOR));

            SwingWorker<List<Benchmark>, Void> worker =
                new SwingWorker<List<Benchmark>, Void>() {
                    protected List<Benchmark> doInBackground() {
                        int[] sizes = {100, 250, 500, 1000, 2000};
                        List<Benchmark> data = new ArrayList<>();

                        for (int n : sizes) {
                            Point[] pts = generatePoints(n, SEED + n);

                            timeBrute(pts);
                            timeDivide(pts);

                            double[] bt = new double[3];
                            double[] dt = new double[3];

                            for (int i = 0; i < 3; i++) {
                                bt[i] = timeBrute(pts);
                                dt[i] = timeDivide(pts);
                            }

                            Arrays.sort(bt);
                            Arrays.sort(dt);

                            data.add(new Benchmark(n, bt[1], dt[1]));
                        }

                        return data;
                    }

                    protected void done() {
                        frame.setCursor(Cursor.getDefaultCursor());

                        try {
                            chartPanel.updateData(get());
                            statusLabel.setText("Benchmark completed.");
                        } catch (Exception e) {
                            statusLabel.setText("Benchmark failed.");
                            JOptionPane.showMessageDialog(
                                frame, e.getMessage(),
                                "Benchmark error", JOptionPane.ERROR_MESSAGE
                            );
                        }
                    }
                };

            worker.execute();
        }

        void exportCSV() {
            if (points.size() < 2) {
                JOptionPane.showMessageDialog(
                    frame, "Add at least two points before exporting."
                );
                return;
            }

            if (result == null) {
                int answer = JOptionPane.showConfirmDialog(
                    frame,
                    "Find the closest pair before exporting?",
                    "Calculate first",
                    JOptionPane.YES_NO_OPTION
                );

                if (answer != JOptionPane.YES_OPTION) return;
                findClosest();

                if (result == null) return;
            }

            JFileChooser chooser = new JFileChooser();
            chooser.setSelectedFile(
                new File("closest_pair_points.csv")
            );

            if (chooser.showSaveDialog(frame) != JFileChooser.APPROVE_OPTION) {
                return;
            }

            File file = chooser.getSelectedFile();

            try (PrintWriter out = new PrintWriter(
                    new OutputStreamWriter(
                        new FileOutputStream(file),
                        java.nio.charset.StandardCharsets.UTF_8
                    ))) {

                out.println("ID,X,Y,ClosestPair");

                for (Point p : points) {
                    boolean closest =
                        p.id == result.p1.id || p.id == result.p2.id;

                    out.printf(
                        Locale.US, "%d,%.8f,%.8f,%s%n",
                        p.id, p.x, p.y, closest
                    );
                }

                statusLabel.setText("CSV exported: " + file.getName());

                JOptionPane.showMessageDialog(
                    frame,
                    "Points exported successfully:\n" + file.getAbsolutePath()
                );

            } catch (IOException e) {
                JOptionPane.showMessageDialog(
                    frame,
                    "Could not save CSV:\n" + e.getMessage(),
                    "Export error",
                    JOptionPane.ERROR_MESSAGE
                );
            }
        }

        void clearResults() {
            countLabel.setText("Points: " + points.size());
            pairLabel.setText("Closest pair: Not calculated");
            distanceLabel.setText("Minimum distance: —");
            bruteLabel.setText("Brute Force: —");
            divideLabel.setText("Divide & Conquer: —");
        }

        void updateView() {
            pointPanel.updateData(
                points.toArray(new Point[0]), result
            );
            countLabel.setText("Points: " + points.size());
        }

        void reset() {
            int answer = JOptionPane.showConfirmDialog(
                frame,
                "Generate a fresh set of 100 points?",
                "Reset",
                JOptionPane.YES_NO_OPTION
            );

            if (answer == JOptionPane.YES_OPTION) {
                generateRandomPoints(100);
                statusLabel.setText("Reset complete.");
            }
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(App::new);
    }
}
