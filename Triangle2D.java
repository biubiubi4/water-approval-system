import java.lang.Math;

//class Main {
//    public static void main(String[] args) {
//        Triangle2D t1 = new Triangle2D(new MyPoint(2.5, 2), new
//                MyPoint(4.2, 3), new MyPoint(5, 3.5));
//        System.out.printf("%.3f\n", t1.getArea());
//        System.out.printf("%.3f\n", t1.getPerimeter());
//        MyPoint p1 = new MyPoint(3,3);
//        System.out.printf("%b\n", t1.contains(p1));
//        System.out.printf("%b\n", t1.contains(new Triangle2D(new MyPoint(2.9, 2), new MyPoint(4, 1),
//                new MyPoint(1, 3.4))));
//        System.out.printf("%b\n", t1.overlaps(new Triangle2D(new MyPoint(2, 5.5), new MyPoint (4,-3),
//                new MyPoint(2, 6.5))));
//    }
//}

public class Triangle2D {
    private MyPoint p1;
    private MyPoint p2;
    private MyPoint p3;

    public Triangle2D() {
        p1 = new MyPoint(0, 0);
        p2 = new MyPoint(1, 1);
        p3 = new MyPoint(2, 5);
    }

    public Triangle2D(MyPoint p1, MyPoint p2, MyPoint p3) {
        this.p1 = p1;
        this.p2 = p2;
        this.p3 = p3;
    }

    public MyPoint getP1() {
        return p1;
    }

    public MyPoint getP2() {
        return p2;
    }

    public MyPoint getP3() {
        return p3;
    }

    public void setP1(MyPoint p1) {
        this.p1 = p1;
    }

    public void setP2(MyPoint p2) {
        this.p2 = p2;
    }

    public void setP3(MyPoint p3) {
        this.p3 = p3;
    }

    public double getArea() {
        double s = (MyPoint.distance(p1, p2) + MyPoint.distance(p1, p3) + MyPoint.distance(p2, p3)) / 2;
        return Math.sqrt(s * (s - MyPoint.distance(p1, p2)) * (s - MyPoint.distance(p1, p3)) * (s - MyPoint.distance(p2, p3)));
    }

    public double getPerimeter() {
        return MyPoint.distance(p1, p2) + MyPoint.distance(p1, p3) + MyPoint.distance(p2, p3);
    }

    public boolean contains(MyPoint p) {
        return new Triangle2D(p1, p2, p).getArea() + new Triangle2D(p1, p3, p).getArea() + new Triangle2D(p3, p2, p).getArea() == getArea();
    }

    public boolean contains(Triangle2D t) {
        return contains(t.p1) && contains(t.p2) && contains(t.p3);
    }

    public boolean overlaps(Triangle2D t) {
        MyPoint[][] lstp = {{p1, p2, p3}, {t.p1, t.p2, t.p3}};
        LineSegment[][] lstl = new LineSegment[2][3];
        for (int i = 0; i < 2; i++) {
            int count = 0;
            for (int j = 0; j < 3; j++) {
                for (int k = j + 1; k < 3; k++) lstl[i][count++] = new LineSegment(lstp[i][j], lstp[i][k]);
            }
        }
        boolean flag = false;
        for (int i = 0; i < 3 && !flag; i++) {
            for (int j = 0; j < 3 && !flag; j++) {
                if (lstl[0][i].intersect(lstl[1][j]) != null) flag = true;
            }
        }
        return flag;
    }
}
